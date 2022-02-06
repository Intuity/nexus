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

    @classmethod
    def symbol(cls, op):
        if   op == Operation.INVERT: return "!"
        elif op == Operation.AND   : return "&"
        elif op == Operation.NAND  : return "!&"
        elif op == Operation.OR    : return "|"
        elif op == Operation.NOR   : return "!|"
        elif op == Operation.XOR   : return "^"
        elif op == Operation.XNOR  : return "!^"
        else: return None

class Gate:
    """ Represents a gate in the design """

    ID = 0

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
        self.id      = Gate.issue_id()
        self.name    = f"{Operation(op).name.upper()}{self.id}"
        self.op      = op
        self.inputs  = inputs[:]
        self.outputs = outputs[:]

    def __repr__(self):
        return (
            type(self).__name__ + "(" + ",".join([str(x) for x in self.inputs])
            + ")"
        )
    def __str__(self): return self.__repr__()

    @classmethod
    def issue_id(cls):
        """ Issue a unique gate ID.

        Returns: Integer ID for this gate
        """
        issued   = Gate.ID
        Gate.ID += 1
        return f"G{issued:03d}"

    @property
    def symbol(self):
        return Operation.symbol(self.op)

    def copy(self):
        """
        Create a copy of this gate with the same name and ID. Note that I/O is
        not copied as connectivity is constructed externally.

        Returns: Instance of Gate (or inherited type), populated as a copy """
        # Create base copy
        if type(self) == Gate:
            new = type(self)(self.op, [], [])
        elif issubclass(type(self), Gate):
            new = type(self)(None, None)
        # Copy over ID and name
        new.id   = self.id
        new.name = self.name
        # Return the copy
        return new

class INVERT(Gate):
    def __init__(self, input=None, output=None):
        inputs  = [input ] if input  else []
        outputs = [output] if output else []
        super().__init__(Operation.INVERT, inputs, outputs)

class AND(Gate):
    def __init__(self, inputs, output):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.AND, inputs, outputs)

class NAND(Gate):
    def __init__(self, inputs, output):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.NAND, inputs, outputs)

class OR(Gate):
    def __init__(self, inputs, output=None):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.OR, inputs, outputs)

class NOR(Gate):
    def __init__(self, inputs, output):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.NOR, inputs, outputs)

class XOR(Gate):
    def __init__(self, inputs, output):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.XOR, inputs, outputs)

class XNOR(Gate):
    def __init__(self, inputs, output):
        if not inputs: inputs = []
        outputs = [output] if output else []
        super().__init__(Operation.XNOR, inputs, outputs)
