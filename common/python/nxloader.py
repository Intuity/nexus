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

from collections import namedtuple

import json
from pathlib import Path

from nxconstants import NodeCommand, NodeLoadInstr, NodeMapOutput

Loaded = namedtuple("Loaded", ["instructions", "mappings"])

class NXLoader:
    """ Parses JSON designs exported by nxcompile """

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

    def load(self, path):
        """ Load a design

        Args:
            path: File handle or path to the JSON description of the design
        """
        # Parse in the JSON description
        if isinstance(path, Path):
            with open(path, "r") as fh:
                model = json.load(fh)
        else:
            model = json.load(path)
        # Pickup the configuration section
        config   = model[NXLoader.DESIGN_CONFIG]
        cfg_rows = config[NXLoader.CONFIG_ROWS]
        cfg_cols = config[NXLoader.CONFIG_COLUMNS]
        # Track what should be loaded to each node
        instrs   = [[[] for _ in range(cfg_cols)] for _ in range(cfg_rows)]
        mappings = [[[] for _ in range(cfg_cols)] for _ in range(cfg_rows)]
        # Start loading the compiled design into the mesh
        nodes = model[NXLoader.DESIGN_NODES]
        for node_data in nodes:
            # Get the row and column of the target node
            n_row = node_data[NXLoader.NODE_ROW]
            n_col = node_data[NXLoader.NODE_COLUMN]
            # Pickup instructions and messages for each node
            # Decode instructions to be loaded
            for raw_instr in node_data[NXLoader.NODE_INSTRS]:
                msg                = NodeLoadInstr()
                msg.header.row     = n_row
                msg.header.column  = n_col
                msg.header.command = NodeCommand.LOAD_INSTR
                msg.instr.unpack(raw_instr)
                instrs[n_row][n_col].append(msg)
            # Decode output mappings to be loaded
            for idx_output, msgs in enumerate(node_data[NXLoader.NODE_MSGS]):
                for tgt_row, tgt_col, tgt_idx, tgt_seq in msgs:
                    msg                = NodeMapOutput()
                    msg.header.row     = n_row
                    msg.header.column  = n_col
                    msg.header.command = NodeCommand.MAP_OUTPUT
                    msg.source_index   = idx_output
                    msg.target_row     = tgt_row
                    msg.target_column  = tgt_col
                    msg.target_index   = tgt_idx
                    msg.target_is_seq  = tgt_seq
                    mappings[n_row][n_col].append(msg)
        return Loaded(instructions=instrs, mappings=mappings)
