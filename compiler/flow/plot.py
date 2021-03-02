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
logging.getLogger("matplotlib").setLevel(logging.WARNING)

import networkx
import matplotlib.pyplot as plt

from ..models.constant import Constant
from ..models.flop import Flop
from ..models.gate import Gate, Operation
from ..models.module import Module
from ..models.port import PortBit

PLOT_COLOURS = [
    "green",
    "blue",
    "violet",
]

def plot_group(flop, inputs, logic, path):
    """ Plot a flop-logic-flop grouping.

    Args:
        flop  : The flop being driven
        inputs: Primary inputs/flop driving logic cloud
        logic : Logic cloud
        path  : Path to write out the rendered PNG
    """
    # Create a graph
    graph = networkx.DiGraph()
    # Work out the max depth
    max_gate_depth  = max([x[1] for x in logic])
    max_input_depth = max([x[1] for x in inputs])
    max_depth       = max((max_gate_depth, max_input_depth))
    # Collect node colours and labels
    colours = []
    labels  = {}
    # Find the earliest (deepest) appearance for each input
    input_first = {}
    for input, depth in inputs:
        if input.name not in input_first:
            input_first[input.name] = (input, depth)
        elif input_first[input.name][1] < depth:
            input_first[input.name] = (input, depth)
    # Create primary input nodes
    for input, depth in input_first.values():
        graph.add_node(input.name, layer=max_depth-depth)
        if isinstance(input, Constant):
            colours.append("red")
            labels[input.name] = "1" if input.value else "0"
        elif isinstance(input, PortBit):
            colours.append("#99ff66")
            labels[input.name] = "I"
        else:
            raise Exception(f"Unknown input {input}")
    # Find the earliest (deepest) appearance for each gate
    gate_first = {}
    for gate, depth in logic:
        if gate.name not in gate_first:
            gate_first[gate.name] = (gate, depth)
        elif gate_first[gate.name][1] < depth:
            gate_first[gate.name] = (gate, depth)
    # Create gate nodes
    for gate, depth in gate_first.values():
        graph.add_node(gate.name, layer=max_depth-depth)
        colours.append("#99ccff")
        labels[gate.name] = gate.symbol
    # Add output node
    graph.add_node(flop.name, layer=max_depth+1)
    colours.append("violet")
    labels[flop.name] = "O"
    # Construct edges
    graph.add_edge(flop.input[0].driver.name, flop.name)
    for gate, _ in logic:
        for in_bit in gate.inputs:
            graph.add_edge(in_bit.name, gate.name)
    # Draw graph
    plt.figure(figsize=(12, 8))
    plt.margins(0)
    plt.axis("off")
    axis = plt.gca()
    axis.set_title(flop.hier_name)
    networkx.draw(
        graph,
        networkx.multipartite_layout(graph, subset_key="layer", align="vertical"),
        width=0.5,
        node_color=colours,
        node_size=200,
        with_labels=True,
        labels=labels,
        ax=axis,
    )
    plt.savefig(path, bbox_inches="tight")
    plt.close()
