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

import click

from nxmodel.manager import Manager
from nxmodel.node import Instruction

@click.command()
@click.option("--listing", type=click.File("w"), help="Dump a text listing of instructions")
@click.argument("design", type=click.File("r"))
def main(listing, design):
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
    # Load the instruction sequences for every node
    nodes = [
        [[] for _c in range(cfg_cols)] for _c in range(cfg_rows)
    ]
    for node_data in model[Manager.DESIGN_NODES]:
        n_row = node_data[Manager.NODE_ROW]
        n_col = node_data[Manager.NODE_COLUMN]
        for raw in node_data[Manager.NODE_INSTRS]:
            nodes[n_row][n_col].append(Instruction(raw))
    # Dump a text-based listing of all instructions
    if listing:
        for row, columns in enumerate(nodes):
            for col, instrs in enumerate(columns):
                listing.write("# " + ("=" * 78 + "\n"))
                listing.write(f"# Row {row:03d}, Column {col:03d}\n")
                listing.write("# " + ("=" * 78 + "\n"))
                listing.write("\n")
                for idx, instr in enumerate(instrs):
                    listing.write(f"{idx:03d}: {instr}\n")
                listing.write("\n")

if __name__ == "__main__":
    main(prog_name="nxdisasm")
