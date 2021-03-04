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
import os

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
    node_colours = []
    node_labels  = {}
    # Find the earliest (deepest) appearance for each input
    input_first = {}
    for input, depth in inputs:
        if input.name not in input_first:
            input_first[input.name] = (input, depth)
        elif input_first[input.name][1] < depth:
            input_first[input.name] = (input, depth)
    # Create primary input nodes
    in_prefix = os.path.commonprefix(list(input_first.keys()))
    in_suffix = os.path.commonprefix([x[::-1] for x in input_first.keys()])[::-1]
    if in_prefix == in_suffix: in_suffix = ""
    for input, depth in input_first.values():
        if isinstance(input, Constant):
            graph.add_node(input.name, layer=max_depth-depth)
            node_colours.append("red")
            node_labels[input.name] = "1" if input.value else "0"
        elif isinstance(input, PortBit):
            graph.add_node(input.name, layer=0) # layer=max_depth-depth)
            node_colours.append("#99ff66")
            short = input.name.replace(in_prefix, "").replace(in_suffix, "")
            if short.strip() == "": short = str(input.index)
            node_labels[input.name] = short
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
        node_colours.append("#99ccff")
        node_labels[gate.name] = gate.symbol
    # Add output node
    graph.add_node(flop.name, layer=max_depth+1)
    node_colours.append("violet")
    node_labels[flop.name] = flop.input.name
    # Draw the basic graph
    plt.figure(figsize=(12, 8))
    plt.margins(0.05)
    plt.axis("off")
    axis = plt.gca()
    if len(in_suffix) > 0:
        axis.set_title(f"{in_prefix}X{in_suffix} -> {flop.input[0].name}")
    else:
        axis.set_title(f"{in_prefix} -> {flop.input[0].name}")
    layout = networkx.multipartite_layout(graph, subset_key="layer", align="vertical")
    networkx.draw_networkx_nodes(
        graph, layout, node_color=node_colours, node_size=200, ax=axis,
    )
    networkx.draw_networkx_labels(graph, layout, labels=node_labels, ax=axis)
    # Construct different edge classes
    input_edges, gate_edges = [], []
    for gate, _ in logic:
        for in_bit in gate.inputs:
            (gate_edges if isinstance(in_bit, Gate) else input_edges).append(
                (in_bit.name, gate.name)
            )
    networkx.draw_networkx_edges(
        graph, layout, edgelist=input_edges, width=0.5, edge_color="green",
        ax=axis,
    )
    networkx.draw_networkx_edges(
        graph, layout, edgelist=gate_edges, width=0.5, edge_color="blue",
        ax=axis,
    )
    networkx.draw_networkx_edges(
        graph, layout, edgelist=[(flop.input[0].driver.name, flop.name)], width=0.5,
        edge_color=("blue" if isinstance(flop.input[0].driver, Gate) else "green"),
        ax=axis,
    )
    # Write to file
    plt.savefig(path, bbox_inches="tight")
    plt.close()
