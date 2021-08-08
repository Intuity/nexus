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
from pathlib import Path
import re

import click
from mako.lookup import TemplateLookup

from nxmodel.manager import Manager
from nxmodel.node import Instruction, Operation

def verilog_safe(val):
    """ Reformat a name to be safe for Verilog """
    return val.translate(val.maketrans(".[", "__", "]"))

@click.command()
@click.option("--listing", type=click.File("w"), help="Dump a text listing of instructions")
@click.option("--verilog", type=click.File("w"), help="Dump a Verilog conversion of the design")
@click.argument("design", type=click.File("r"))
def main(listing, verilog, design):
    """ Disassemble a compiled design.

    Arguments:\n
        DESIGN: Path to the compiled design.
    """
    # Read in the design
    model = json.load(design)
    # Pickup the configuration section
    config   = model[Manager.DESIGN_CONFIG]
    cfg_rows = config[Manager.CONFIG_ROWS]
    cfg_cols = config[Manager.CONFIG_COLUMNS]
    cfg_node = config[Manager.CONFIG_NODE]
    # Extract per node configuration
    nc_inputs    = cfg_node[Manager.CFG_ND_INPUTS]
    nc_outputs   = cfg_node[Manager.CFG_ND_OUTPUTS]
    nc_registers = cfg_node[Manager.CFG_ND_REGS]
    # Load the instruction sequences for every node
    nodes = [
        [[] for _c in range(cfg_cols)] for _r in range(cfg_rows)
    ]
    node_inputs = [
        [{} for _c in range(cfg_cols)] for _r in range(cfg_cols)
    ]
    node_outputs = [
        [{} for _c in range(cfg_cols)] for _r in range(cfg_cols)
    ]
    outputs = {}
    for node_data in model[Manager.DESIGN_NODES]:
        n_row = node_data[Manager.NODE_ROW]
        n_col = node_data[Manager.NODE_COLUMN]
        # Load the instruction sequence
        out_idx = 0
        for instr_idx, raw in enumerate(node_data[Manager.NODE_INSTRS]):
            instr = Instruction(raw)
            nodes[n_row][n_col].append(instr)
            if instr.is_output:
                node_outputs[n_row][n_col][out_idx] = instr_idx
                out_idx += 1
        # Load the node inputs
        for idx_output, msgs in enumerate(node_data[Manager.NODE_MSGS]):
            for tgt_row, tgt_col, tgt_idx, tgt_seq in msgs:
                # Skip entries talking to 'fake' nodes
                if tgt_row >= cfg_rows: continue
                # Link input -> output
                node_inputs[tgt_row][tgt_col][tgt_idx] = (
                    n_row, n_col, idx_output, tgt_seq
                )
    for name, bits in model[Manager.DESIGN_REPORTS][Manager.DSG_REP_OUTPUTS].items():
        for idx_bit, (src_row, src_col, src_idx, _, _, _, is_seq) in enumerate(bits):
            if not name in outputs: outputs[name] = {}
            outputs[name][idx_bit] = (src_row, src_col, src_idx, is_seq)
    # Create a template lookup
    tmpl_lkp = TemplateLookup(directories=[Path(__file__).parent / "templates"])
    # Dump a text-based listing of all instructions
    if listing:
        listing.write(tmpl_lkp.get_template("disasm.txt").render(
            nodes=nodes,
        ))
    # Dump a Verilog implementation of the instructions
    if verilog:
        verilog.write(tmpl_lkp.get_template("disasm.v").render(
            # Node configurations
            cfg_nd_ins =nc_inputs,
            cfg_nd_outs=nc_outputs,
            cfg_nd_regs=nc_registers,
            # Instructions and mappings
            nodes       =nodes,
            node_inputs =node_inputs,
            node_outputs=node_outputs,
            outputs     =outputs,
            # Helper functions
            verilog_safe=verilog_safe,
            # Constants
            **Operation.__members__,
            verilog_op_map={
                Operation.AND: "&", Operation.NAND: "&",
                Operation.OR : "|", Operation.NOR : "|",
                Operation.XOR: "^", Operation.XNOR: "^",
            },
        ))

if __name__ == "__main__":
    main(prog_name="nxdisasm")
