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

from itertools import groupby
import logging
from operator import itemgetter

log = logging.getLogger("parser.module")

from .base import Base
from .bit import Bit
from .cell import Cell
from .constant import Constant
from .net import Net
from .port import Port, PortDirection
from .select import Select
from .signal import Signal

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
        self.bits       = {}
        # Kick off the parse
        self.parse()

    @property
    def ports(self): return self.inputs + self.outputs + self.inouts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        desc = [f"// Module Declaration"]
        desc.append(f"module {self.name} #(")
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
            desc.append(f"// Type: {cell.type}, Model: {cell.model}")
            desc.append(str(cell))
            desc.append("")
        desc.append("endmodule")
        desc.append("")
        desc.append("// Connectivity")
        for key, bit in self.bits.items():
            desc.append(
                f"// - {bit.id:3d} - signals: " +
                ", ".join([(
                    (x.parent.safe_name + "." + x.safe_name)
                    if isinstance(x, Port) else
                    x.safe_name
                ) for x in bit.signals])
            )
        return "\n".join(desc)

    def link_bit(self, key, signal):
        """
        Link any type of signal to either a Constant or Bit

        Args:
            key   : String to create a Constant, or Int to create a bit
            signal: Link a signal to the

        Returns: Bit or Constant depending on input
        """
        if isinstance(key, str):
            const = Constant(int(key, 2), 1)
            const.link(signal)
            return const
        elif not isinstance(key, int):
            raise Exception("Bit key must be string or integer")
        elif key not in self.bits:
            self.bits[key] = Bit(key)
        self.bits[key].link(signal)
        return self.bits[key]

    def get_bit_driver(self, bit):
        """ Work out the driver of a bit.

        Args:
            bit: Either an instance of Bit or a bit ID

        Returns: The signal instance driving the bit
        """
        # Convert bit ID to a Bit instance
        if not isinstance(bit, Bit): bit = self.bits[bit]
        # Identify all drivers in list
        drivers = []
        for sig in bit.signals:
            if not isinstance(sig, Port): continue
            if (
                (sig.parent == self and sig.direction == PortDirection.INPUT ) or
                (sig.parent != self and sig.direction == PortDirection.OUTPUT)
            ):
                drivers.append(sig)
        # Check for multi-drive
        if len(drivers) > 1:
            raise Exception(f"Bit {bit.id} appears to be multi-driven")
        # Check for no drive
        elif len(drivers) == 0:
            raise Exception(f"Bit {bit.id} appears to be undriven")
        # Return the driver
        return drivers[0]

    def get_bit_targets(self, bit):
        """ Get all of the targets for a bit.

        Args:
            bit: Either an instance of Bit or a bit ID

        Returns: The signal instances driven by the bit.
        """
        # Convert bit ID to a Bit instance
        if not isinstance(bit, Bit): bit = self.bits[bit]
        # Identify all drivers in list
        targets = []
        for sig in bit.signals:
            if (
                (isinstance(sig, Port) and (
                    (sig.parent == self and sig.direction == PortDirection.INPUT ) or
                    (sig.parent != self and sig.direction == PortDirection.OUTPUT)
                )) or isinstance(sig, Net)
            ):
                targets.append(sig)
        # Check for no targets
        if len(targets) == 0:
            raise Exception(f"Bit {bit.id} appears to drive nothing")
        # Return the targets
        return targets

    def get_signal(self, bit_ids):
        """ Concatenate a signal together given a list of bits.

        Args:
            bit_ids: List of bit IDs
        """
        # First lookup all bits
        signals = []
        for bit_id in bit_ids:
            if isinstance(bit_id, str):
                signals.append((bit_id, Constant(int(bit_id, 2), 1), 0))
            else:
                bit = self.get_bit(bit_id)
                signals.append((
                    bit_id, bit.driver.signal, bit.driver.signal.map(bit)
                ))
        # Group into contiguous groups by the driving signal
        groups = { k: list(g) for k, g in groupby(signals, lambda x: x[1]) }
        # Assemble selections
        selects = []
        for port, components in groups.items():
            selects.append(Select(port, *[x[2] for x in components]))
        return selects

    def parse(self):
        """ Parse the raw module data into a structured representation """
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
            dirx      = PortDirection[data[Module.PORT_DIRECTION].upper()]
            port      = Port(key, dirx, self, len(data[Module.PORT_BITS]), [])
            port.bits = [self.link_bit(x, port) for x in data[Module.PORT_BITS]]
            {
                PortDirection.INPUT : self.inputs,
                PortDirection.OUTPUT: self.outputs,
                PortDirection.INOUT : self.inouts,
            }[dirx].append(port)
        # Read in the nets
        raw_nets = self.raw.get(Module.NETS, {})
        for key, data in raw_nets.items():
            hide_name  = (True if data[Module.NET_HIDE_NAME] else False)
            bits       = data[Module.NET_BITS]
            attributes = data[Module.NET_ATTRIBUTES]
            net        = Net(key, len(bits), [], hide=hide_name)
            net.bits   = [self.link_bit(x, net) for x in bits]
            self.nets.append(net)
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
            self.cells.append(Cell(
                key, c_type, model, self, (True if hide_name else False)
            ))
            for p_key, p_val in parameters.items():
                self.cells[-1].add_parameter(p_key, int(p_val, 2))
            for a_key, a_val in attributes.items():
                self.cells[-1].set_attribute(a_key, a_val)
            for p_key, p_dirx in port_dirx.items():
                p_dirx    = PortDirection[p_dirx.upper()]
                p_conns   = connections[p_key]
                port      = self.cells[-1].add_port(p_key, p_dirx, len(bits), [])
                port.bits = [self.link_bit(x, port) for x in p_conns]
