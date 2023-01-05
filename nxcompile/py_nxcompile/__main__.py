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

from collections import defaultdict
import json
import logging
import math
import pathlib
import random

import click

from nxisa import dump_asm, dump_hex
import nxcompile

from .grouper import group_logic
from .compiler import Node

@click.command()
@click.option("--seed",             type=int,     default=  0,   help="Specify a random seed")
@click.option("--mesh-max-rows",    type=int,     default= 16,   help="Maximum rows in the mesh")
@click.option("--mesh-max-columns", type=int,     default= 16,   help="Maximum columns in the mesh")
@click.option("--node-max-inputs",  type=int,     default=256,   help="Maximum inputs per node")
@click.option("--node-max-outputs", type=int,     default=256,   help="Maximum outputs per node")
@click.option("--node-max-flops",   type=int,     default=256,   help="Maximum flops per node")
@click.option("--node-max-gates",   type=int,     default=512,   help="Maximum gates per node")
@click.option("--node-max-instr",   type=int,     default=1024,  help="Maximum instructions per node")
@click.option("--only-optimise",    is_flag=True, default=False, help="Only optimise design")
@click.option("--only-partition",   is_flag=True, default=False, help="Optimise and partition")
@click.option("--log",              type=click.Path(dir_okay=False), default=None, help="Log to file")
@click.option("--verbose",          is_flag=True, default=False, help="Enable verbose logging")
@click.argument("netlist", type=click.Path(exists=True, dir_okay=False))
@click.argument("outdir",  type=click.Path(file_okay=False))
def main(seed             : int,
         mesh_max_rows    : int,
         mesh_max_columns : int,
         node_max_inputs  : int,
         node_max_outputs : int,
         node_max_flops   : int,
         node_max_gates   : int,
         node_max_instr   : int,
         only_optimise    : bool,
         only_partition   : bool,
         log              : str,
         verbose          : bool,
         netlist          : str,
         outdir           : str) -> None:
    # Setup logging for C++ objects
    nxcompile.setup_logging(verbose)
    logging.basicConfig(level=[logging.INFO, logging.DEBUG][verbose],
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    if log:
        logging.getLogger().addHandler(logging.FileHandler(log, mode="w", encoding="utf-8"))

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

    # Optional early exit (post-optimisation)
    if only_optimise: return

    # Form partitions
    logging.info("Forming groups of logic")
    partitions = group_logic(module, limits={ "inputs" : node_max_inputs,
                                              "outputs": node_max_outputs,
                                              "flops"  : node_max_flops,
                                              "gates"  : node_max_gates })

    # Optional early exit (post-partitioning)
    if only_partition: return

    # Create output directory
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Form a roughly square mesh of nodes
    # NOTE: Partition indexes are discarded as they are not contiguous by this point
    columns = int(min(mesh_max_columns, math.ceil(math.sqrt(len(partitions)))))
    rows    = int(min(mesh_max_rows,    math.ceil(len(partitions) / columns)))
    nodes   = [Node(x, (i // columns), (i % columns), node_max_instr) for i, x in enumerate(partitions)]

    # Create a lookup from source flops -> nodes that require them
    flop_lookup = defaultdict(list)
    for node in nodes:
        for flop in node.partition.src_flops:
            flop_lookup[flop.name].append(node)

    # Compile instruction sequences for each node
    logging.info("Node compilation")
    registry = {
        "design"    : netlist,
        "seed"      : seed,
        "rows"      : rows,
        "columns"   : columns,
        "partitions": len(partitions),
        "nodes"     : []
    }
    port_offset = 0
    for idx, node in enumerate(nodes):
        stream, port_map, mem_map = node.compile(flop_lookup, port_offset)
        port_offset += len(port_map)
        dump_asm(stream, outdir / f"r{node.row}c{node.column}.asm")
        dump_hex(stream, outdir / f"r{node.row}c{node.column}.hex")
        registry["nodes"].append({
            "id"    : idx,
            "row"   : node.row,
            "column": node.column,
            "index" : node.partition.index,
            "gates" : len(node.partition.all_gates),
            "flops" : len(node.partition.tgt_flops),
            "ports" : [[y[0].name for y in x] for x in port_map],
            "memory": mem_map,
            "asm"   : (outdir / f"r{node.row}c{node.column}.asm").absolute().as_posix(),
            "hex"   : (outdir / f"r{node.row}c{node.column}.hex").absolute().as_posix(),
        })

    with open(outdir / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=4)

if __name__ == "__main__":
    main(prog_name="nxcompile")
