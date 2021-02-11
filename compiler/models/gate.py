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

class Operation(IntEnum):
    INVERT = 0
    AND    = 1
    NAND   = 2
    OR     = 3
    NOR    = 4
    XOR    = 5
    XNOR   = 6

class Gate:
    """ Represents a gate in the design """

    def __init__(self, op, inputs, outputs):
        """ Initialise the Operation instance.

        Args:
            op     : The operation this gate performs (from Operation)
            inputs : List of input signals to the gate
            outputs: List of output signals from the gate
        """
        assert op in Operation
        assert isinstance(inputs, list)
        assert isinstance(outputs, list)
        self.op      = op
        self.inputs  = inputs[:]
        self.outputs = outputs[:]

class INVERT(Gate):
    def __init__(self, input, output):
        super().__init__(OpAction.INVERT, [input], [output])

class AND(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.AND, inputs, [output])

class NAND(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.AND, inputs, [output])

class OR(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.OR, inputs, [output])

class NOR(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.NOR, inputs, [output])

class XOR(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.XOR, inputs, [output])

class XNOR(Gate):
    def __init__(self, inputs, output):
        super().__init__(OpAction.XNOR, inputs, [output])

