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
    # Mesh configuration
    CONFIG_ROWS    = "rows"
    CONFIG_COLUMNS = "columns"
    # Per-node configuration
    NODE_ROW       = "row"
    NODE_COLUMN    = "column"
    NODE_INSTRS    = "instructions"
    NODE_IN_MAP    = "input_map"
    NODE_OUT_MAP   = "output_map"
    # Node input mapping
    IN_MAP_SRC_ROW = "source_row"
    IN_MAP_SRC_COL = "source_column"
    IN_MAP_SRC_POS = "source_bit"
    IN_MAP_TGT_POS = "target_bit"
    IN_MAP_STATE   = "is_state"
    # Node output mapping
    OUT_MAP_POS       = "position"
    OUT_MAP_TGT_A_ROW = "row_a"
    OUT_MAP_TGT_A_COL = "column_a"
    OUT_MAP_TGT_B_ROW = "row_b"
    OUT_MAP_TGT_B_COL = "column_b"
    OUT_MAP_BROADCAST = "broadcast"
    OUT_MAP_DECAY     = "decay"

    def __init__(self, env, mesh):
        """ Initialise the Manager.

        Args:
            env : SimPy environment
            mesh: The Nexus mesh model
        """
        super().__init__(env)
        self.mesh     = mesh
        self.outbound = Pipe(self.env, 1, 1)
        self.queue    = []
        self.tx_loop  = self.env.process(self.transmit())
        self.gen_tick = self.env.process(self.tick())

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
        cfg_cols = config[Manager.CONFIG_COLS]
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
            for in_idx, mapping in enumerate(node_data[Manager.NODE_IN_MAP]):
                self.queue.append(ConfigureInput(
                    self.env, n_row, n_col,
                    mapping[IN_MAP_SRC_ROW], mapping[IN_MAP_SRC_COL],
                    mapping[IN_MAP_SRC_POS], mapping[IN_MAP_STATE],
                ))
            # Setup output mappings for the node
            for mapping in node_data[MANAGER.NODE_OUT_MAP]:
                self.queue.append(ConfigureOutput(
                    self.env, n_row, n_col, mapping[OUT_MAP_POS],
                    mapping[OUT_MAP_TGT_A_ROW], mapping[OUT_MAP_TGT_A_COL],
                    mapping[OUT_MAP_TGT_B_ROW], mapping[OUT_MAP_TGT_B_COL],
                    mapping[OUT_MAP_BROADCAST], mapping[OUT_MAP_DECAY],
                ))

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

    def tick(self):
        """ Generate ticks """
        tick_count = 0
        while True:
            # Wait a cycle
            yield self.env.timeout(1)
            # If the queue is busy, don't generate a tick yet
            if self.queue: continue
            # Check all nodes in the mesh are idle
            idle = True
            for row in self.mesh.nodes:
                for node in row:
                    idle &= node.idle
                    if not idle: break
                if not idle: break
            if not idle: continue
            # Generate the tick
            tick_count += 1
            self.info(f"Generating tick {tick_count}")
            for row in self.mesh.nodes:
                for node in row:
                    node.tick()
