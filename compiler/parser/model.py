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

from enum import IntEnum
import logging

log = logging.getLogger("parser.model")

class ModelOperations(IntEnum):
    PORT  = 0
    NPORT = 1
    AND   = 3
    NAND  = 4
    TRUE  = 5
    FALSE = 6

class ModelNode:
    """ Represents an individual operation in the model """

    def __init__(self, index, op, inputs, outputs):
        """ Initialise the node instance.

        Args:
            index  : Node index within the model
            op     : Operation the node performs (from ModelOperations)
            inputs : Input signal tuples (PORT, IDX)
            outputs: Output signal tuples (PORT, IDX)
        """
        assert op in ModelOperations
        self.index   = index
        self.inputs  = inputs[:]
        self.outputs = outputs[:]

    def __repr__(self):
        return (
            f"[{self.index:03d}] {type(self).__name__:5s} - Inputs: "
            + ", ".join([str(x) for x in self.inputs]) + " Outputs: " +
            ", ".join([str(x) for x in self.outputs])
        )

class Port(ModelNode):
    def __init__(self, index, in_port, in_bit, outputs):
        super().__init__(index, ModelOperations.PORT, [(in_port, in_bit)], outputs)

class NPort(ModelNode):
    def __init__(self, index, in_port, in_bit, outputs):
        super().__init__(index, ModelOperations.NPORT, [(in_port, in_bit)], outputs)

class AND(ModelNode):
    def __init__(self, index, in_idx_a, in_idx_b, outputs):
        super().__init__(index, ModelOperations.AND, [in_idx_a, in_idx_b], outputs)

class NAND(ModelNode):
    def __init__(self, index, in_idx_a, in_idx_b, outputs):
        super().__init__(index, ModelOperations.NAND, [in_idx_a, in_idx_b], outputs)

class ConstantOne(ModelNode):
    def __init__(self, index, outputs):
        super().__init__(index, ModelOperations.TRUE, [], outputs)

class ConstantZero(ModelNode):
    def __init__(self, index, outputs):
        super().__init__(index, ModelOperations.FALSE, [], outputs)

class Model:
    """ Representation of an AIG model from Yosys JSON """

    # Node types
    NODE_PORT  = "port"  # Takes the value of a bit from an input port
    NODE_NPORT = "nport" # Takes the inverted value of a bit from an input port
    NODE_AND   = "and"   # ANDs together two selected bits
    NODE_NAND  = "nand"  # NANDs together two selected bits
    NODE_TRUE  = "true"  # Constant value of 1
    NODE_FALSE = "false" # Constant value of 0

    def __init__(self, name, raw):
        """ Initialise the Model instance.

        Args:
            name: Name of the model
            raw : The raw list from the Yosys JSON output
        """
        assert isinstance(name, str)
        assert isinstance(raw,  list)
        self.name  = name
        self.raw   = raw
        self.nodes = []
        self.parse()

    def __repr__(self):
        desc = [f"Model {self.name} - has {len(self.nodes)} nodes"]
        for node in self.nodes:
            desc.append(" - " + str(node))
        return "\n".join(desc)

    def parse(self):
        """ Parse the raw model data into a structured representation """
        self.nodes = []
        def build_port_tuples(p_list):
            return [(p_list[x], p_list[x+1]) for x in range(0, len(p_list), 2)]
        for idx, (n_type, *n_args) in enumerate(self.raw):
            if n_type == Model.NODE_PORT:
                self.nodes.append(Port(
                    idx, n_args[0], n_args[1], build_port_tuples(n_args[2:])
                ))
            elif n_type == Model.NODE_NPORT:
                self.nodes.append(NPort(
                    idx, n_args[0], n_args[1], build_port_tuples(n_args[2:])
                ))
            elif n_type == Model.NODE_AND:
                self.nodes.append(AND(
                    idx, n_args[0], n_args[1], build_port_tuples(n_args[2:])
                ))
            elif n_type == Model.NODE_NAND:
                self.nodes.append(NAND(
                    idx, n_args[0], n_args[1], build_port_tuples(n_args[2:])
                ))
            elif n_type == Model.NODE_TRUE:
                self.nodes.append(ConstantOne(idx, build_port_tuples(n_args)))
            elif n_type == Model.NODE_FALSE:
                self.nodes.append(ConstantZero(idx, build_port_tuples(n_args)))
            else:
                raise Exception(
                    f"Unrecognised node '{n_type}' in model AIG description"
                )
