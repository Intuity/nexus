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

import logging
from pathlib import Path

import click

from .debug import export_rtl
from .flow import compile, elaborate, export, flatten, simplify
from .parser import Parser

log = logging.getLogger("compiler")
log.setLevel(logging.INFO)

@click.command()
# Mesh configuration
@click.option("-r", "--rows", type=int, default=4, help="Number of rows in the mesh")
@click.option("-c", "--cols", type=int, default=4, help="Number of columns in the mesh")
# Node configuration
@click.option("--node-inputs",    type=int, default= 32, help="Inputs per node")
@click.option("--node-outputs",   type=int, default= 32, help="Outputs per node")
@click.option("--node-registers", type=int, default=  8, help="Working registers")
@click.option("--node-slots",     type=int, default=512, help="Max instructions per node")
# Debug options
@click.option("--show-modules",  count=True,        help="Print out parsed modules")
@click.option("--show-models",   count=True,        help="Print out parsed models")
@click.option("--debug",         count=True,        help="Print debugging messages")
@click.option("--export-simple", type=click.Path(), help="Export the simplified model to Verilog")
@click.option("--export-flat",   type=click.Path(), help="Export the flattened model to Verilog")
# Positional arguments
@click.argument("input", type=click.Path(exists=True))
@click.argument("top")
@click.argument("output", type=click.Path(file_okay=True, dir_okay=False))
def main(
    # Mesh configuration
    rows, cols,
    # Node configuration
    node_inputs, node_outputs, node_registers, node_slots,
    # Debug options
    show_modules, show_models, debug, export_simple, export_flat,
    # Positional arguments
    input, top, output,
):
    """ Compiles Yosys JSON export into a Nexus instruction schedule

    Arguments:

        input : Path to the Yosys JSON export

        top   : The name of the top-level module in the design

        output: Output file for the compiled design, to use with model or RTL
    """
    # Alter the logging verbosity
    if debug: log.setLevel(logging.DEBUG)

    # Run the parse step on the Yosys JSON input
    log.info(f"Parsing Yosys JSON file: {input}")
    parser = Parser(input)
    parser.parse()
    if show_modules:
        for module in parser.modules: print(module)
    if show_models:
        for model in parser.models: print(model)

    # Check for the requested top
    log.info(f"Looking for design top-level '{top}'")
    found = [x for x in parser.modules if x.name == top]
    if len(found) != 1:
        log.error(f"Could not resolve top-level '{top}' within JSON design")
        return False
    top_mod = found[0]

    # Map the Yosys JSON model into internal model
    log.info(f"Elaborating from top-level '{top_mod.name}'")
    model = elaborate(
        top    =top_mod,
        modules=parser.modules,
        models =parser.models,
    )

    # Flatten the module
    log.info("Flattening hierarchy")
    flat = flatten(model)

    # Optionally write out the flattened model
    if export_flat:
        log.info(f"Writing out flattened model to {export_flat}")
        export_rtl(flat, export_flat)

    # Simplify the module (propagate constants, etc)
    log.info("Simplifying module")
    smpl = simplify(flat)

    # Optionally write out the simplified model
    if export_simple:
        log.info(f"Writing out simplified model to {export_simple}")
        export_rtl(smpl, export_simple)

    # Compile onto mesh
    log.info("Compiling design onto mesh")
    c_instrs, c_msgs, c_state_map, c_output_map = compile(
        smpl, rows=rows, columns=cols,
        node_inputs=node_inputs, node_outputs=node_outputs,
        node_registers=node_registers, node_slots=node_slots,
    )

    # Export to JSON
    log.info(f"Exporting compiled design to {output}")
    export(
        output,
        rows, cols,
        node_inputs, node_outputs, node_registers, node_slots,
        c_instrs, c_msgs, c_state_map, c_output_map,
    )

if __name__ == "__main__":
    main()
