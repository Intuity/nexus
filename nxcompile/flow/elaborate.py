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

log = logging.getLogger("elaborate")

# Import Yosys models
from ..parser.module import Module as YModule
from ..parser import model as yosys_model
from ..parser.bit import Bit as YBit
from ..parser.constant import Constant as YConstant
from ..parser.model import Model as YModel
from ..parser.port import Port as YPort

# Import compiler models
from ..models.constant import Constant as NexusConstant
from ..models import gate as nexus_gate
from ..models.flop import Flop as NexusFlop
from ..models.module import Module as NexusModule
from ..models.port import Port as NexusPort
from ..models.port import PortBit as NexusPortBit
from ..models.port import PortDirection as NexusPortDirection

def _build_cell_model(cell, model):
    """ Build up a chain of operations from an AIG (AND-INVERTER Graphs).

    Args:
        cell : Cell of this model
        model: The AIG model

    Returns: The operation chain
    """
    # Build a module to represent the cell
    mod = NexusModule(cell.name, cell.type)
    # Build ports to match the cell description
    for key, y_port in cell.ports.items():
        mod.add_port(
            y_port.name, NexusPortDirection(y_port.direction), y_port.width,
        )
    # Build up the signal chains
    points = []
    for idx, node in enumerate(model.nodes):
        inputs = []
        for item in node.inputs:
            if isinstance(item, tuple):
                inputs.append(mod.ports[item[0]][item[1]])
            else:
                inputs += points[item]
        outputs = [mod.ports[x][y] for x, y in node.outputs]
        gate    = None
        if isinstance(node, yosys_model.Port):
            pass
        elif isinstance(node, yosys_model.NPort):
            assert len(inputs) == 1
            gate = nexus_gate.INVERT(inputs[0], None)
        elif isinstance(node, yosys_model.AND):
            assert len(inputs) == 2
            gate = nexus_gate.AND(inputs, outputs[0] if outputs else None)
        elif isinstance(node, yosys_model.NAND):
            assert len(inputs) == 2
            gate = nexus_gate.NAND(inputs, outputs[0] if outputs else None)
        elif isinstance(node, yosys_model.ConstantOne):
            inputs = [NexusConstant(1)]
        elif isinstance(node, yosys_model.ConstantZero):
            inputs = [NexusConstant(0)]
        # If 'gate' is populated, connect to inputs
        if gate:
            for bit in inputs:
                if isinstance(bit, nexus_gate.Gate):
                    bit.outputs.append(gate)
                elif isinstance(bit, NexusPortBit):
                    bit.add_target(gate)
                else:
                    raise Exception(f"Unknown input type {bit}")
            for bit in outputs:
                bit.driver = gate
        # If 'gate' not populated, but 'outputs' are - then connect in -> out
        else:
            for in_bit, out_bit in zip(inputs, outputs):
                out_bit.driver = in_bit
        # Store the point
        points.append([gate] if gate else inputs)
        # Attach the gate to the module
        if gate:
            mod.add_child(gate)
    # Return the cell module
    return mod

def _build_module(src, ymodules, ymodels, instance=None):
    """
    Build a compiler Module from a Yosys Module, will be called recursively to
    build up the full tree.

    Args:
        src     : The Yosys Module to elaborate
        ymodules: Lookup for Yosys Modules to resolve child instances
        ymodels : Lookup for Yosys Models to resolve complex cells
        instance: Name of this instance (otherwise assume it matches type)

    Returns: Instance of compiler Module
    """
    log.info(f"Building compiler module from Yosys module '{src.name}'")
    # Sanity checks
    assert isinstance(src, YModule)
    assert len([x for x in ymodules.values() if not isinstance(x, YModule)]) == 0
    assert len([x for x in ymodels.values()  if not isinstance(x, YModel )]) == 0
    assert isinstance(instance, str) or instance == None
    # If no name provided, adopt the module type
    if not instance: instance = src.name
    # Build the boundary
    nmod = NexusModule(instance, src.name)
    log.info(f"Adding input ports to {nmod.name}")
    for yport in src.inputs: nmod.add_input(yport.name, yport.width)
    log.info(f"Adding output ports to {nmod.name}")
    for yport in src.outputs: nmod.add_output(yport.name, yport.width)
    log.info(f"Adding inout ports to {nmod.name}")
    for yport in src.inouts: nmod.add_inout(yport.name, yport.width)
    # Look-up cells and child module definitions
    log.info(f"Parsing cells of {nmod.name}")
    for cell in src.cells:
        # Complex functions
        if cell.model:
            log.info(
                f" - Cell {cell.name} - Type: {cell.type}, Model: {cell.model}"
            )
            if cell.model not in ymodels:
                raise Exception(f"Failed to resolve cell model '{cell.model}'")
            # Get the I/O for the operation
            nmod.add_child(_build_cell_model(cell, ymodels[cell.model]))
        # Nested modules
        elif cell.type in ymodules:
            log.info(f" - Cell {cell.name} - Type: {cell.type}")
            nmod.add_child(_build_module(
                ymodules[cell.type], ymodules, ymodels, instance=cell.name,
            ))
        # Flop primitive
        elif cell.type == "$adff":
            log.info(f" - Cell {cell.name} is a primitive '{cell.type}'")
            nmod.add_child(NexusFlop(
                cell.name,
                NexusPort("CLK",  NexusPortDirection.INPUT,  1),
                NexusPort("ARST", NexusPortDirection.INPUT,  1),
                NexusPort("D",    NexusPortDirection.INPUT,  cell.ports["D"].width),
                NexusPort("Q",    NexusPortDirection.OUTPUT, cell.ports["Q"].width),
            ))
        # Unknown
        else:
            raise Exception(
                f"Unknown type for cell '{cell.name}' of type '{cell.type}'"
            )
    # Build out connectivity from boundary input ports
    for port in src.inputs:
        drv_port = nmod.ports[port.name]
        for bit in port.bits:
            drv_bit = drv_port[bit.index]
            for target in bit.targets:
                if not isinstance(target.parent, YPort): continue
                tgt_mod  = (
                    nmod if (target.parent.parent == src) else
                    nmod.children[target.parent.parent.name]
                )
                tgt_port = tgt_mod.ports[target.parent.name]
                tgt_bit  = tgt_port[target.index]
                tgt_bit.driver = drv_bit
                drv_bit.add_target(tgt_bit)
    # Build out connectivity from child ports
    for child in src.cells:
        drv_child = nmod.children[child.name]
        for port in child.ports.values():
            drv_port = drv_child.ports[port.name]
            for bit in port.bits:
                drv_bit = drv_port[bit.index]
                if port.is_input:
                    if not isinstance(bit.driver, YConstant): continue
                    n_const = NexusConstant(bit.driver.value)
                    drv_bit.driver = n_const
                    n_const.add_target(drv_bit)
                elif port.is_output:
                    for target in bit.targets:
                        if not isinstance(target.parent, YPort): continue
                        tgt_mod  = (
                            nmod if (target.parent.parent == src) else
                            nmod.children[target.parent.parent.name]
                        )
                        tgt_port = tgt_mod.ports[target.parent.name]
                        tgt_bit  = tgt_port[target.index]
                        tgt_bit.driver = drv_bit
                        drv_bit.add_target(tgt_bit)
    # Return the constructed module
    return nmod

def elaborate(top, modules, models):
    """ Convert parsed Yosys JSON into the compiler's internal representation.

    Args:
        top    : The top level Yosys Module to convert
        modules: List of Yosys Modules to use when elaborating
        models : List of Yosys Models for complex cells

    Return: Instance of Module (from models.module) containing elaborated design
    """
    # Sanity checks
    assert isinstance(top,     YModule)
    assert isinstance(modules, list   )
    assert isinstance(models,  list   )
    assert len([x for x in modules if not isinstance(x, YModule)]) == 0
    assert len([x for x in models  if not isinstance(x, YModel )]) == 0
    # Convert module and model lists into lookups
    mod_lkp = { x.name: x for x in modules }
    mdl_lkp = { x.name: x for x in models  }
    # Start building from the top
    log.info(f"Elaborating from top '{top.name}'")
    mod = _build_module(top, ymodules=mod_lkp, ymodels=mdl_lkp)
    # Return the elaborated model
    return mod
