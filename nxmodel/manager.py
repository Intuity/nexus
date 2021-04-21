# Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re
from timeit import default_timer as timer

import simpy

from .base import Base
from .pipe import Pipe
from .message import LoadInstruction, ConfigureInput, ConfigureOutput
from .node import Instruction

class Manager(Base):
    """
    Provides a manager for a Nexus mesh - takes care of loading instructions and
    generating ticks.
    """

    # Main sections
    DESIGN_CONFIG  = "configuration"
    DESIGN_NODES   = "nodes"
    DESIGN_REPORTS = "reports"
    # Mesh configuration
    CONFIG_ROWS    = "rows"
    CONFIG_COLUMNS = "columns"
    CONFIG_NODE    = "node"
    CFG_ND_INPUTS  = "inputs"
    CFG_ND_OUTPUTS = "outputs"
    CFG_ND_REGS    = "registers"
    CFG_ND_SLOTS   = "slots"
    # Per-node configuration
    NODE_ROW      = "row"
    NODE_COLUMN   = "column"
    NODE_INSTRS   = "instructions"
    NODE_IN_HNDL  = "in_handling"
    NODE_OUT_HNDL = "out_handling"
    # Node input handling
    IN_HNDL_SRC_ROW = "source_row"
    IN_HNDL_SRC_COL = "source_column"
    IN_HNDL_SRC_POS = "source_bit"
    IN_HNDL_TGT_POS = "target_bit"
    IN_HNDL_STATE   = "is_state"
    # Node output handling
    OUT_HNDL_POS       = "position"
    OUT_HNDL_TGT_A_ROW = "row_a"
    OUT_HNDL_TGT_A_COL = "column_a"
    OUT_HNDL_TGT_B_ROW = "row_b"
    OUT_HNDL_TGT_B_COL = "column_b"
    OUT_HNDL_BROADCAST = "broadcast"
    OUT_HNDL_DECAY     = "decay"
    # Design reports
    DSG_REP_STATE   = "state"
    DSG_REP_OUTPUTS = "outputs"

    def __init__(self, env, mesh, cycles, break_on_idle):
        """ Initialise the Manager.

        Args:
            env          : SimPy environment
            mesh         : The Nexus mesh model
            cycles       : How many cycles to run for
            break_on_idle: Launch a PDB session every time the mesh is idle
        """
        super().__init__(env)
        # Capture variables
        self.mesh          = mesh
        self.cycles        = cycles
        self.break_on_idle = break_on_idle
        # Create interface and state
        self.outbound = Pipe(self.env, 1, 1)
        self.queue    = []
        self.observer = []
        self.tx_loop  = self.env.process(self.transmit())
        self.gen_tick = self.env.process(self.tick())
        self.complete = self.env.event()

    def add_observer(self, cb):
        """ Add a callback to an observer to be notified of a tick event.

        Args:
            cb: Callback function
        """
        self.observer.append(cb)

    def load(self, design):
        """ Load a design into the mesh.

        Args:
            design: File handle to the JSON description of the design
        """
        # Parse in the JSON description
        model = json.load(design)
        # Pickup the configuration section
        config   = model[Manager.DESIGN_CONFIG]
        cfg_rows = config[Manager.CONFIG_ROWS]
        cfg_cols = config[Manager.CONFIG_COLUMNS]
        # Check that the mesh matches
        assert cfg_rows == self.mesh.rows
        assert cfg_cols == self.mesh.columns
        # Start loading the compiled design into the mesh
        nodes = model[Manager.DESIGN_NODES]
        for node_data in nodes:
            # Get the row and column of the target node
            n_row = node_data[Manager.NODE_ROW]
            n_col = node_data[Manager.NODE_COLUMN]
            # Load instructions into the node
            for slot, raw_instr in enumerate(node_data[Manager.NODE_INSTRS]):
                instr = Instruction(raw_instr)
                self.queue.append(LoadInstruction(
                    self.env, n_row, n_col, slot, instr
                ))
            # Setup input mappings for the node
            for mapping in node_data[Manager.NODE_IN_HNDL]:
                self.queue.append(ConfigureInput(
                    self.env, n_row, n_col,
                    mapping[Manager.IN_HNDL_SRC_ROW], mapping[Manager.IN_HNDL_SRC_COL],
                    mapping[Manager.IN_HNDL_SRC_POS], mapping[Manager.IN_HNDL_TGT_POS],
                    mapping[Manager.IN_HNDL_STATE],
                ))
            # Setup output mappings for the node
            for mapping in node_data[Manager.NODE_OUT_HNDL]:
                self.debug(f"Queueing ({len(self.queue)}) output config for {n_row}, {n_col}")
                self.queue.append(ConfigureOutput(
                    self.env, n_row, n_col, mapping[Manager.OUT_HNDL_POS],
                    (tgt_a_row := mapping.get(Manager.OUT_HNDL_TGT_A_ROW, 0)),
                    (tgt_a_col := mapping.get(Manager.OUT_HNDL_TGT_A_COL, 0)),
                    # NOTE: If B outputs don't exist, match A values, this will
                    #       suppress a second message being emitted
                    mapping.get(Manager.OUT_HNDL_TGT_B_ROW, tgt_a_row),
                    mapping.get(Manager.OUT_HNDL_TGT_B_COL, tgt_a_col),
                    mapping.get(Manager.OUT_HNDL_BROADCAST, False),
                    mapping.get(Manager.OUT_HNDL_DECAY,     0),
                ))
        # Set input names
        rgx_pos = re.compile(r"^R([0-9]+)C([0-9]+)I([0-9]+)")
        for entry, name in model[Manager.DESIGN_REPORTS][Manager.DSG_REP_STATE].items():
            row, col, idx = [int(x) for x in rgx_pos.match(entry).groups()]
            self.mesh[row, col].input_names[idx] = name
        return model[Manager.DESIGN_REPORTS][Manager.DSG_REP_OUTPUTS]

    def transmit(self):
        """ Transmit any queued messages """
        while True:
            # If queue is empty, wait for a cycle and then loop
            if not self.queue:
                yield self.env.timeout(1)
                continue
            # Pop the next message and transmit it
            self.debug("Transmitting message into mesh")
            msg = self.queue.pop(0)
            yield self.env.process(self.outbound.push(msg))

    def idle(self):
        """ Determine if mesh is completely idle.

        Returns: True if idle, False if busy
        """
        idle = True
        for row in self.mesh.nodes:
            for node in row:
                idle &= node.idle
                if not idle: break
            if not idle: break
        return idle

    def tick(self):
        """ Generate ticks """
        cycle = 0
        start = timer()
        while cycle < self.cycles:
            # Wait a cycle
            yield self.env.timeout(1)
            # If the queue is busy, don't generate a tick yet
            if self.queue: continue
            # Check all nodes in the mesh are idle
            if not self.idle(): continue
            # If requested, break for debug
            if self.break_on_idle:
                import pdb; pdb.set_trace()
            # Count number of cycles
            # NOTE: As cycles can be blocked by busy queues or busy nodes, the
            #       increment of cycle must be postponed.
            cycle += 1
            self.info(f"Generating tick {cycle}")
            # First notify any observers
            for observer in self.observer: observer()
            # Now notify all nodes in the mesh
            for row in self.mesh.nodes:
                for node in row:
                    node.tick()
        # Wait for mesh to go idle
        yield self.env.timeout(1)
        while not self.idle(): yield self.env.timeout(1)
        # Print statistics
        clock_ticks = self.env.now
        real_time   = timer() - start
        print("")
        print("# " + "=" * 78)
        print("# Simulation Statistics")
        print("# " + "=" * 78)
        print("#")
        print(f"# Simulated Cycles   : {self.cycles}")
        print(f"# Elapsed Clock Ticks: {clock_ticks}")
        print(f"# Elapsed Real Time  : {real_time:0.02f} seconds")
        print(f"# Cycles/second      : {self.cycles/real_time:0.02f}")
        print("#")
        print("# " + "=" * 78)
        print("")
        # Stop the simulation
        self.complete.succeed()
