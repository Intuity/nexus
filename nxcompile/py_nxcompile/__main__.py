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
import logging
import math
import pathlib
import random

import click

from nxisa import dump_asm, dump_hex
import nxcompile

from .grouper import group_logic
from .nodecompiler import Node

@click.command()
@click.option("--seed",             type=int, default=  0, help="Specify a random seed")
@click.option("--node-max-inputs",  type=int, default=256, help="Maximum inputs per node")
@click.option("--node-max-outputs", type=int, default=256, help="Maximum outputs per node")
@click.option("--node-max-flops",   type=int, default=256, help="Maximum flops per node")
@click.option("--node-max-gates",   type=int, default=512, help="Maximum gates per node")
@click.argument("netlist", type=click.Path(exists=True, dir_okay=False))
@click.argument("outdir",  type=click.Path(file_okay=False))
def main(seed             : int,
         node_max_inputs  : int,
         node_max_outputs : int,
         node_max_flops   : int,
         node_max_gates   : int,
         netlist          : str,
         outdir           : str) -> None:
    # Setup logging for C++ objects
    nxcompile.setup_logging()

    # Seed random number generation
    logging.info("Setting random seed to %(seed)d", { "seed": seed })
    random.seed(seed)

    # Parse and optimise netlist
    logging.info("Parsing netlist '%(path)s'", { "path": netlist })
    module = nxcompile.NXParser.parse_from_file(netlist)
    logging.info("Running initial sanity optimisation")
    nxcompile.optimise_sanity(module, True)
    logging.info("RTL stats prior to pruning/propagating:\n" + nxcompile.dump_rtl_stats(module))
    nxcompile.optimise_prune(module)
    nxcompile.optimise_propagate(module)
    nxcompile.optimise_prune(module)
    logging.info("RTL stats after pruning/propagating:\n" + nxcompile.dump_rtl_stats(module))
    nxcompile.optimise_sanity(module, False)

    # Form partitions
    logging.info("Forming groups of logic")
    partitions = group_logic(module, limits={ "inputs" : node_max_inputs,
                                              "outputs": node_max_outputs,
                                              "flops"  : node_max_flops,
                                              "gates"  : node_max_gates })

    # Create output directory
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Compile instruction sequences for each node
    logging.info("Node compilation")
    registry = {
        "design"    : netlist,
        "seed"      : seed,
        "rows"      : math.ceil(math.sqrt(len(partitions))),
        "columns"   : math.ceil(math.sqrt(len(partitions))),
        "partitions": len(partitions),
        "nodes"     : []
    }
    compilers = [Node(x) for x in partitions]
    for compiler in compilers:
        stream, port_map, mem_map = compiler.compile()
        dump_asm(stream, outdir / f"{compiler.partition.id}.asm")
        dump_hex(stream, outdir / f"{compiler.partition.id}.hex")
        registry["nodes"].append({
            "id"    : compiler.partition.id,
            "row"   : (compiler.partition.index // 8),
            "column": (compiler.partition.index  % 8),
            "index" : compiler.partition.index,
            "gates" : len(compiler.partition.all_gates),
            "flops" : len(compiler.partition.tgt_flops),
            "ports" : [[y[0].name for y in x] for x in port_map],
            "memory": mem_map,
            "asm"   : (outdir / f"{compiler.partition.id}.asm").absolute().as_posix(),
            "hex"   : (outdir / f"{compiler.partition.id}.hex").absolute().as_posix(),
        })

    with open(outdir / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=4)

if __name__ == "__main__":
    main(prog_name="nxcompile")
