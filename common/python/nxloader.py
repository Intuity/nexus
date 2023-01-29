# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import List

from nxconstants import Instruction, OutputLookup, OutputMapping

@dataclass
class NodeState:
    instructions : List[Instruction] = field(default_factory=list)
    loopback     : int = 0
    lookup       : List[OutputLookup] = field(default_factory=list)
    mappings     : List[OutputMapping] = field(default_factory=list)

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
    NODE_ROW      = "row"
    NODE_COLUMN   = "column"
    NODE_INSTRS   = "instructions"
    NODE_LOOPBACK = "loopback"
    NODE_OUTPUTS  = "outputs"
    # Output mapping entries
    MAPPING_ROW    = "row"
    MAPPING_COLUMN = "column"
    MAPPING_INDEX  = "index"
    MAPPING_IS_SEQ = "is_seq"

    def __init__(self, path):
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
        config        = model[NXLoader.DESIGN_CONFIG]
        self.cfg_rows = config[NXLoader.CONFIG_ROWS]
        self.cfg_cols = config[NXLoader.CONFIG_COLUMNS]
        self.cfg_outs = config[NXLoader.CONFIG_NODE][NXLoader.CFG_ND_OUTPUTS]
        # Track state for each node
        self.state = [
            [NodeState() for _ in range(self.cfg_cols)] for _ in range(self.cfg_rows)
        ]
        # Start loading the compiled design into the mesh
        nodes = model[NXLoader.DESIGN_NODES]
        for node_data in nodes:
            # Get the row and column of the target node
            n_row = node_data[NXLoader.NODE_ROW]
            n_col = node_data[NXLoader.NODE_COLUMN]
            # Get point to the state object
            state = self.state[n_row][n_col]
            # Read in all of the instructions
            for raw in node_data[NXLoader.NODE_INSTRS]:
                instr = Instruction()
                instr.unpack(raw)
                state.instructions.append(instr)
            # Pickup the loopback mapping
            state.loopback = node_data[NXLoader.NODE_LOOPBACK]
            # Read in all of the output mappings
            counts = {}
            for idx, entries in enumerate(node_data[NXLoader.NODE_OUTPUTS]):
                counts[idx] = len(entries)
                for entry in entries:
                    mapping = OutputMapping(
                        row   =entry[NXLoader.MAPPING_ROW],
                        column=entry[NXLoader.MAPPING_COLUMN],
                        index =entry[NXLoader.MAPPING_INDEX],
                        is_seq=entry[NXLoader.MAPPING_IS_SEQ],
                    )
                    state.mappings.append(mapping)
            # Generate output lookups
            offset = len(state.instructions) + self.cfg_outs
            for idx in range(self.cfg_outs):
                lookup = OutputLookup(
                    active=(counts.get(idx, 0) > 0),
                    start =offset,
                    stop  =(offset + counts.get(idx, 0) - 1),
                )
                state.lookup.append(lookup)
                offset += counts.get(idx, 0)
