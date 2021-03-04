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

from .parser import Parser
from .flow.elaborate import elaborate
from .flow.flatten import flatten
from .flow.group import group_logic
from .flow.plot import plot_group
from .flow.simplify import simplify_group
from .flow.prune import prune
from .flow.compile import compile

log = logging.getLogger("compiler")

@click.command()
# Debug options
@click.option("--show-modules", count=True,        help="Print out parsed modules")
@click.option("--show-models",  count=True,        help="Print out parsed models")
@click.option("--plot-groups",  type=click.Path(), help="Plot out flop-logic-flop groups")
# Positional arguments
@click.argument("input")
@click.argument("top")
def main(
    # Debug options
    show_modules, show_models, plot_groups,
    # Positional arguments
    input, top,
):
    """ Compiles Yosys JSON export into a Nexus instruction schedule

    Arguments:

        input: Path to the Yosys JSON export
        top  : The name of the top-level module in the design
    """
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
    flat = flatten(model.copy())

    # Form flop-logic-flop groups
    log.info("Grouping logic")
    groups         = group_logic(flat)
    grp_gate_count = [len(x[2]) for x in groups]

    # Simplify logic in groups, optimising out constants
    log.info(f"Simplifying {len(groups)} groups")
    simplified = [simplify_group(*x) for x in groups]

    # Plot pre and post simplify
    if plot_groups:
        log.info(f"Plotting {len(groups)} groups")
        plot_groups = Path(plot_groups)
        plot_groups.mkdir(parents=True, exist_ok=True)
        for idx, (pre, post) in enumerate(zip(grp_gate_count, simplified)):
            log.info(f" - {idx} - #ORIG: {pre}, #SMPL: {len(post[2])}")
            plot_group(*post, plot_groups / f"post_{idx}.png")

    # Prune dead logic
    log.info("Pruning dead logic")
    prune(flat)

    # Compile onto mesh
    log.info("Compiling design onto mesh")
    compile(flat, simplified)

    import pdb; pdb.set_trace()

if __name__ == "__main__":
    main()
