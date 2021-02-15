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
        self.ports      = []
        self.nets       = []
        self.cells      = []
        # Kick off the parse
        self.parse()

    @property
    def inputs(self): return (x for x in self.ports if x.is_input)
    @property
    def outputs(self): return (x for x in self.ports if x.is_output)
    @property
    def inouts(self): return (x for x in self.ports if x.is_inout)

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
        return "\n".join(desc)

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
        # Create a bit lookup to track drivers and targets
        bit_lookup = {}
        def add_driver(bit_id, bit):
            assert isinstance(bit_id, int) and isinstance(bit, Bit)
            if not bit_id in bit_lookup: bit_lookup[bit_id] = ([], [])
            bit_lookup[bit_id][0].append(bit)
            # Link any known targets to this driver
            for tgt in bit_lookup[bit_id][1]:
                tgt.driver = bit
                bit.add_target(tgt)
        def add_target(bit_id, bit):
            assert isinstance(bit_id, int) and isinstance(bit, Bit)
            if not bit_id in bit_lookup: bit_lookup[bit_id] = ([], [])
            bit_lookup[bit_id][1].append(bit)
            # Link any known drivers to this target
            for drv in bit_lookup[bit_id][0]:
                drv.add_target(bit)
                bit.driver = drv
        # Read in the ports
        raw_ports = self.raw.get(Module.PORTS, {})
        for key, data in raw_ports.items():
            dirx = PortDirection[data[Module.PORT_DIRECTION].upper()]
            port = Port(key, dirx, self, len(data[Module.PORT_BITS]))
            self.ports.append(port)
            for bit_id, bit in zip(data[Module.PORT_BITS], port.bits):
                if   port.is_input : add_driver(bit_id, bit)
                elif port.is_output: add_target(bit_id, bit)
        # Read in the nets
        raw_nets = self.raw.get(Module.NETS, {})
        for key, data in raw_nets.items():
            hide_name  = (True if data[Module.NET_HIDE_NAME] else False)
            attributes = data[Module.NET_ATTRIBUTES]
            net        = Net(key, len(data[Module.NET_BITS]), hide=hide_name)
            for a_key, a_val in attributes.items():
                net.set_attribute(a_key, a_val)
            for bit_id, bit in zip(data[Module.NET_BITS], net.bits):
                add_target(bit_id, bit)
            self.nets.append(net)
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
                port = self.cells[-1].add_port(
                    p_key, PortDirection[p_dirx.upper()], len(connections[p_key])
                )
                for bit_id, bit in zip(connections[p_key], port.bits):
                    # If the value is a string - this is a constant
                    if isinstance(bit_id, str):
                        bit.driver = Constant(int(bit_id))
                    # If the value is an integer - this is a bit ID
                    else:
                        if   port.is_input : add_target(bit_id, bit)
                        elif port.is_output: add_driver(bit_id, bit)
        # Detect bits without drivers or targets
        dangling = 0
        for bit_id, (drivers, targets) in bit_lookup.items():
            if len(drivers) == 0 or len(targets) == 0:
                dangling += 1
                log.warn(
                    f"Bit {bit_id} - has {len(drivers)} drivers and "
                    f"{len(targets)} targets"
                )
                if len(drivers) > 0:
                    log.warn("Drivers: " + ", ".join((
                        f"{x.parent.parent.name}.{x.parent.name}" for x in drivers
                    )))
                if len(targets) > 0:
                    log.warn("Targets: " + ", ".join((
                        f"{x.parent.parent.name}.{x.parent.name}" for x in targets
                    )))
        if dangling > 0: raise Exception(f"Detected {dangling} dangling bits")
