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
from pathlib import Path
from timeit import default_timer as timer

import simpy

from .base import Base
from .pipe import Pipe
from .message import LoadInstruction, ConfigureOutput
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
    NODE_ROW    = "row"
    NODE_COLUMN = "column"
    NODE_INSTRS = "instructions"
    NODE_MSGS   = "messages"
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
        self.outbound = Pipe(self.env, 1, 1) if self.env else None
        self.queue    = []
        self.observer = []
        self.loaded   = []
        self.tx_loop  = self.env.process(self.transmit()) if self.env else None
        self.gen_tick = self.env.process(self.tick()) if self.env else None
        self.complete = self.env.event() if self.env else None
        self.is_idle  = self.env.event() if self.env else None
        self.on_tick  = self.env.event() if self.env else None

    def add_observer(self, cb):
        """ Add a callback to an observer to be notified of a tick event.

        Args:
            cb: Callback function
        """
        self.observer.append(cb)

    def load(self, design):
        """ Load a design into the mesh.

        Args:
            design: File handle or Path to the JSON description of the design
        """
        # Parse in the JSON description
        if isinstance(design, Path):
            with open(design, "r") as fh:
                model = json.load(fh)
        else:
            model = json.load(design)
        # Pickup the configuration section
        self.config = model[Manager.DESIGN_CONFIG]
        cfg_rows    = self.config[Manager.CONFIG_ROWS]
        cfg_cols    = self.config[Manager.CONFIG_COLUMNS]
        # Check that the mesh matches
        if self.mesh:
            assert cfg_rows == self.mesh.rows, \
                f"Serialised design requires {cfg_rows} rows"
            assert cfg_cols == self.mesh.columns, \
                f"Serialised design requires {cfg_cols} columns"
        # Track what should be loaded to each node
        self.loaded = [[[] for _ in range(cfg_cols)] for _ in range(cfg_rows)]
        # Start loading the compiled design into the mesh
        nodes = model[Manager.DESIGN_NODES]
        for node_data in nodes:
            # Get the row and column of the target node
            n_row = node_data[Manager.NODE_ROW]
            n_col = node_data[Manager.NODE_COLUMN]
            # Pickup instructions and messages for each node
            node_instrs = node_data[Manager.NODE_INSTRS]
            node_msgs = node_data[Manager.NODE_MSGS]
            self.debug(
                f"Queueing {len(node_instrs)} instructions and "
                f"{sum([len(x) for x in node_msgs])} output messages for "
                f"{n_row}, {n_col}"
            )
            # Load instructions into the node
            for raw_instr in node_instrs:
                instr = Instruction(raw_instr)
                self.queue.append(LoadInstruction(
                    self.env, n_row, n_col, instr
                ))
                self.loaded[n_row][n_col].append(instr)
            # Setup output mappings for the node
            for idx_output, msgs in enumerate(node_msgs):
                # Skip empty output slots
                if not msgs: continue
                # Debug logging
                # Unpack and queue each message
                for tgt_row, tgt_col, tgt_idx, tgt_seq in msgs:
                    self.queue.append(ConfigureOutput(
                        self.env, n_row, n_col, idx_output, tgt_row, tgt_col,
                        tgt_idx, tgt_seq
                    ))
        # Set input names
        rgx_pos = re.compile(r"^R([0-9]+)C([0-9]+)I([0-9]+)")
        if self.mesh:
            for entry, name in model[Manager.DESIGN_REPORTS][Manager.DSG_REP_STATE].items():
                row, col, idx = [int(x) for x in rgx_pos.match(entry).groups()]
                self.mesh[row, col].input_names[idx] = name
        return model[Manager.DESIGN_REPORTS][Manager.DSG_REP_OUTPUTS]

    def check_loaded(self):
        """ Check every loaded instruction """
        self.info("Checking all instructions loaded correctly")
        for row, columns in enumerate(self.loaded):
            for col, instrs in enumerate(columns):
                node_ops = self.mesh[row, col].instrs
                assert len(node_ops) == len(instrs), \
                    f"{row:03d}.{col:03d} Different number of instructions G: " \
                    f"{len(node_ops)} != E: {len(instrs)}"
                for idx, (got, exp) in enumerate(zip(node_ops, instrs)):
                    assert got == exp, \
                        f"{row:03d}.{col:03d} Instruction {idx} differs G: " \
                        f"{got} != E: {exp}"
        self.info("All OK!")

    def transmit(self):
        """ Transmit any queued messages """
        while True:
            # If queue is empty, wait for a cycle and then loop
            if not self.queue:
                yield self.env.timeout(1)
                continue
            # Pop the next message and transmit it
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
        self.is_idle.succeed()
        self.is_idle = self.env.event()
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
            # If this is the first time idle, check the loaded instructions
            if cycle == 0: self.check_loaded()
            # If requested, break for debug
            if self.break_on_idle:
                import pdb; pdb.set_trace()
            # Count number of cycles
            # NOTE: As cycles can be blocked by busy queues or busy nodes, the
            #       increment of cycle must be postponed.
            cycle += 1
            if (cycle % 10) == 0: self.info(f"Generating tick {cycle}")
            # First notify any observers
            for observer in self.observer: observer()
            # Trigger event
            self.on_tick.succeed()
            self.on_tick = self.env.event()
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
        print(f"# Ticks Per Cycle    : {clock_ticks / self.cycles:0.02f}")
        print(f"# Elapsed Real Time  : {real_time:0.02f} seconds")
        print(f"# Cycles/second      : {self.cycles/real_time:0.02f}")
        print("#")
        print("# " + "=" * 78)
        print("")
        # Stop the simulation
        self.complete.succeed()
