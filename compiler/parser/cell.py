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

from .base import Base
from .port import Port, PortDirection

class Cell(Base):
    """ Represents a cell primitive in the design """

    def __init__(self, name, type, model, hide=False):
        """ Initialise the Cell instance.

        Args:
            name : Name of the cell
            type : Type of the cell
            model: Model of the cell
            hide : Whether the name of the cell should be shown
        """
        super().__init__(name)
        # Check and store attributes
        assert isinstance(type,  str)
        assert isinstance(model, str) or model == None
        assert isinstance(hide,  bool)
        self.type  = type
        self.model = model
        self.hide  = hide
        # Create stores
        self.parameters = {}
        self.inputs     = []
        self.outputs    = []
        self.inouts     = []

    @property
    def ports(self): return self.inputs + self.outputs + self.inouts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        desc = [f"{self.type} {self.safe_name} #("]
        for idx, (key, val) in enumerate(self.parameters.items()):
            desc.append(
                "    " + (", " if idx > 0 else "  ") + f".{key}('d{val})"
            )
        desc.append(") (")
        for idx, port in enumerate(self.ports):
            desc.append(
                "    " + (", " if idx > 0 else "  ") +  f".{port.safe_name}(...)"
            )
        desc.append(");")
        return "\n".join(desc)

    def add_parameter(self, key, value):
        """ Add a parameter to the cell.

        Args:
            key  : Name of parameter, must be a string
            value: Value of the parameter, must be an integer
        """
        assert isinstance(key,   str)
        assert isinstance(value, int)
        self.parameters[key] = value

    def add_port(self, name, direction, width, bits):
        """ Add a port to the cell.

        Args:
            name : Name of the port
            width: Width of the port
            bits : Bit IDs that connect to the port
        """
        {
            PortDirection.INPUT : self.inputs,
            PortDirection.OUTPUT: self.outputs,
            PortDirection.INOUT : self.inouts,
        }[direction].append(Port(name, direction, width, bits))
