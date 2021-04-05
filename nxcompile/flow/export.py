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
from operator import sub

# Main sections
DESIGN_CONFIG = "configuration"
DESIGN_NODES  = "nodes"
# Mesh configuration
CONFIG_ROWS    = "rows"
CONFIG_COLUMNS = "columns"
CONFIG_NODE    = "node"
CFG_ND_INPUTS  = "inputs"
CFG_ND_OUTPUTS = "outputs"
CFG_ND_REGS    = "registers"
CFG_ND_SLOTS   = "slots"
# Per-node configuration
NODE_ROW     = "row"
NODE_COLUMN  = "column"
NODE_INSTRS  = "instructions"
NODE_IN_MAP  = "input_map"
NODE_OUT_MAP = "output_map"
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

def export(
    output,
    mesh_rows, mesh_columns,
    node_inputs, node_outputs, node_registers, node_slots,
    instructions, input_map, output_map,
):
    """
    Export the compiled design to a file for loading into the architectural
    model or the RTL design.

    Args:
        output        : Path to the output file to write
        mesh_rows     : Number of rows in the mesh
        mesh_columns  : Number of columns in the mesh
        node_inputs   : Number of inputs per node
        node_outputs  : Number of outputs per node
        node_registers: Number of working registers per node
        node_slots    : Number of instruction slots per node
        instructions  : Instruction sequences for every node
        input_map     : Input handling for every node
        output_map    : Output handling for every node
    """
    # Assemble the model
    model = {
        DESIGN_CONFIG: {
            CONFIG_ROWS   : mesh_rows,
            CONFIG_COLUMNS: mesh_columns,
            CONFIG_NODE   : {
                CFG_ND_INPUTS : node_inputs,
                CFG_ND_OUTPUTS: node_outputs,
                CFG_ND_REGS   : node_registers,
                CFG_ND_SLOTS  : node_slots,
            },
        },
        DESIGN_NODES: [],
    }
    # Build up per-node information
    for (row, col), (_, _, op_seq) in instructions.items():
        # Pickup the input and output handling for this node
        inputs  = input_map[row, col]
        outputs = output_map[row, col]
        # Start building up a node description
        node = {
            NODE_ROW    : row,
            NODE_COLUMN : col,
            NODE_INSTRS : op_seq,
            NODE_IN_MAP : (in_map  := []),
            NODE_OUT_MAP: (out_map := []),
        }
        # Build up the input mapping
        for in_idx, (src_node, src_pos, is_state) in inputs.items():
            node[NODE_IN_MAP].append({
                IN_MAP_SRC_ROW: src_node.position[0],
                IN_MAP_SRC_COL: src_node.position[1],
                IN_MAP_SRC_POS: src_pos,
                IN_MAP_TGT_POS: in_idx,
                IN_MAP_STATE  : is_state,
            })
        # Build up the output mapping
        for out_idx, messages in outputs.items():
            if len(messages) > 2:
                # Work out distances to all target nodes
                distances = [
                    sum(map(abs, map(sub, x.position, (row, col)))) for x in messages
                ]
                node[NODE_OUT_MAP].append({
                    OUT_MAP_POS      : out_idx,
                    OUT_MAP_BROADCAST: True,
                    OUT_MAP_DECAY    : max(distances),
                })
            elif len(messages) > 0:
                node[NODE_OUT_MAP].append({
                    OUT_MAP_POS      : out_idx,
                    OUT_MAP_TGT_A_ROW: messages[0].position[0],
                    OUT_MAP_TGT_A_COL: messages[0].position[1],
                })
                if len(messages) > 1:
                    node[NODE_OUT_MAP][-1][OUT_MAP_TGT_B_ROW] = messages[1].position[0]
                    node[NODE_OUT_MAP][-1][OUT_MAP_TGT_B_COL] = messages[1].position[1]
        # Append node into the model
        model[DESIGN_NODES].append(node)
    # Write the model to file
    with open(output, "w") as fh:
        json.dump(model, fh, indent=4)
