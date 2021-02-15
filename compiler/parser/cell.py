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
from .constant import Constant
from .net import Net
from .port import Port, PortDirection

class Cell(Base):
    """ Represents a cell primitive in the design """

    def __init__(self, name, type, model, parent, hide=False):
        """ Initialise the Cell instance.

        Args:
            name  : Name of the cell
            type  : Type of the cell
            model : Model of the cell
            parent: Parent Module instance
            hide  : Whether the name of the cell should be shown
        """
        super().__init__(name)
        # Check and store attributes
        from .module import Module
        assert isinstance(type,  str)
        assert isinstance(model, str) or model == None
        assert isinstance(parent, Module)
        assert isinstance(hide,  bool)
        self.type   = type
        self.model  = model
        self.parent = parent
        self.hide   = hide
        # Create stores
        self.parameters = {}
        self.ports      = []

    @property
    def inputs(self): return (x for x in self.ports if x.is_input)
    @property
    def outputs(self): return (x for x in self.ports if x.is_output)
    @property
    def inouts(self): return (x for x in self.ports if x.is_inout)

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
            port_str = (
                "    " + (", ." if idx > 0 else "  .") + port.safe_name + "({ "
            )
            for idx, bit in enumerate(port.bits):
                if idx > 0: port_str += ", "
                if port.is_input and isinstance(bit.driver, Constant):
                    port_str += f"1'b{bit.driver.value}"
                elif port.is_input:
                    port_str += f"{bit.driver.parent.safe_name}[{bit.driver.index}]"
                elif port.is_output:
                    port_str += f"{bit.targets[0].parent.safe_name}[{bit.targets[0].index}]"
                else:
                    port_str += "???"
            desc.append(port_str + " })")
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

    def add_port(self, name, direction, width):
        """ Add a port to the cell.

        Args:
            name : Name of the port
            width: Width of the port
        """
        port = Port(name, direction, self, width)
        self.ports.append(port)
        return port
