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

log = logging.getLogger("parser.module")

from .base import Base
from .cell import Cell
from .constant import Constant
from .net import Net
from .port import Port, PortDirection

class Module(Base):
    """ Representation of a Module from Yosys JSON """

    # Top-level attributes
    ATTRIBUTES     = "attributes"
    PARAM_DEF_VALS = "parameter_default_values"
    PORTS          = "ports"
    NETS           = "netnames"
    CELLS          = "cells"

    # Port attributes
    PORT_DIRECTION = "direction"
    PORT_BITS      = "bits"
    PORT_INPUT     = "input"
    PORT_OUTPUT    = "output"
    PORT_INOUT     = "inout"

    # Net attributes
    NET_HIDE_NAME  = "hide_name"
    NET_BITS       = "bits"
    NET_ATTRIBUTES = "attributes"

    # Cell attributes
    CELL_HIDE_NAME       = "hide_name"
    CELL_TYPE            = "type"
    CELL_MODEL           = "model"
    CELL_PARAMETERS      = "parameters"
    CELL_ATTRIBUTES      = "attributes"
    CELL_PORT_DIRECTIONS = "port_directions"
    CELL_CONNECTIONS     = "connections"

    def __init__(self, name, raw):
        """ Initialise the Module instance.

        Args:
            name: Name of the module
            raw : The raw dictionary from the Yosys JSON output
        """
        super().__init__(name)
        # Check and store raw data
        assert isinstance(raw,  dict)
        self.raw  = raw
        # Attributes
        self.parameters = {}
        self.inputs     = []
        self.outputs    = []
        self.inouts     = []
        self.nets       = []
        self.cells      = []
        # Kick off the parse
        self.parse()

    @property
    def ports(self): return self.inputs + self.outputs + self.inouts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        desc = [f"module {self.name} #("]
        for idx, (key, val) in enumerate(self.parameters.items()):
            desc.append(
                "    " + (", " if idx > 0 else "  ") +
                f"parameter {key} = 'd{val:d}"
            )
        desc.append(") (")
        for idx, port in enumerate(self.ports):
            desc.append(
                "    " + (", " if idx > 0 else "  ") +
                f"{PortDirection(port.direction).name.lower():6s} [{port.width-1:3d}:0] {port.safe_name}"
            )
        desc.append(");")
        desc.append("")
        for net in self.nets:
            desc.append(
                f"wire [{net.width-1:3d}:0] {net.safe_name};"
            )
        desc.append("")
        for cell in self.cells:
            desc.append(str(cell))
            desc.append("")
        desc.append("endmodule")
        return "\n".join(desc)

    def parse(self):
        """ Parse the raw model data into a structured representation """
        # Capture attributes
        raw_attrs = self.raw.get(Module.ATTRIBUTES, {})
        for key, val in raw_attrs.items():
            self.set_attribute(key, val)
        # Read in the default parameters
        raw_params = self.raw.get(Module.PARAM_DEF_VALS, {})
        for key, val in raw_params.items():
            self.parameters[key] = int(val, 2)
        # Read in the ports
        raw_ports = self.raw.get(Module.PORTS, {})
        for key, data in raw_ports.items():
            dirx = data[Module.PORT_DIRECTION]
            bits = data[Module.PORT_BITS]
            {
                Module.PORT_INPUT : self.inputs,
                Module.PORT_OUTPUT: self.outputs,
                Module.PORT_INOUT : self.inouts,
            }[dirx].append(
                Port(key, PortDirection[dirx.upper()], len(bits), bits)
            )
        # Read in the nets
        raw_nets = self.raw.get(Module.NETS, {})
        for key, data in raw_nets.items():
            hide_name  = data[Module.NET_HIDE_NAME]
            bits       = data[Module.NET_BITS]
            attributes = data[Module.NET_ATTRIBUTES]
            self.nets.append(Net(
                key, len(bits), bits, (True if hide_name else False),
            ))
            for a_key, a_val in attributes.items():
                self.nets[-1].set_attribute(a_key, a_val)
        # Read in cells
        raw_cells = self.raw.get(Module.CELLS, {})
        for key, data in raw_cells.items():
            hide_name   = data[Module.CELL_HIDE_NAME]
            c_type      = data[Module.CELL_TYPE]
            model       = data.get(Module.CELL_MODEL, None)
            parameters  = data[Module.CELL_PARAMETERS]
            attributes  = data[Module.CELL_ATTRIBUTES]
            port_dirx   = data[Module.CELL_PORT_DIRECTIONS]
            connections = data[Module.CELL_CONNECTIONS]
            self.cells.append(
                Cell(key, c_type, model, (True if hide_name else False))
            )
            for p_key, p_val in parameters.items():
                self.cells[-1].add_parameter(p_key, int(p_val, 2))
            for a_key, a_val in attributes.items():
                self.cells[-1].set_attribute(a_key, a_val)
            for p_key, p_dirx in port_dirx.items():
                p_conns = connections[p_key]
                bits    = []
                for bit in p_conns:
                    bits.append(
                        Constant(int(bit, 2), 1) if isinstance(bit, str) else bit
                    )
                self.cells[-1].add_port(
                    p_key, PortDirection[p_dirx.upper()], len(bits), bits
                )
