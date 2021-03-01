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

from .constant import Constant
from .gate import Gate
from .port import Port, PortBit, PortDirection

class Module:
    """ Represents a module in the hierarchy """

    def __init__(self, name, type, parent=None):
        """ Initialise the Module instance.

        Args:
            name  : Name of the module
            type  : Type of the module
            parent: Parent module of this module
        """
        assert isinstance(name, str)
        assert isinstance(type, str)
        assert isinstance(parent, Module) or parent == None
        self.name     = name
        self.type     = type
        self.parent   = parent
        self.ports    = {}
        self.children = {}

    @property
    def inputs(self): return (x for x in self.ports.values() if x.is_input)
    @property
    def outputs(self): return (x for x in self.ports.values() if x.is_output)
    @property
    def inouts(self): return (x for x in self.ports.values() if x.is_inout)

    def add_raw_port(self, port):
        """ Add a new Port instance to the module.

        Args:
            port: Instance of Port to attach
        """
        assert isinstance(port, Port)
        if port.name in self.ports:
            raise Exception(f"Already have a port called '{port.name}'")
        # Link this module to the port
        port.parent = self
        # Attach the port to the module
        self.ports[port.name] = port

    def add_port(self, name, direction, width):
        """ Add a new port to the module.

        Args:
            name     : Name of the port
            direction: Direction of the port
            width    : Width of the port

        Returns: New port instance
        """
        port = Port(name, direction, width, self)
        self.add_raw_port(port)
        return port

    def add_input(self, name, width):
        """ Add a new input port to the module.

        Args:
            name : Name of the port
            width: Width of the port

        Returns: New port instance
        """
        return self.add_port(name, PortDirection.INPUT, width)

    def add_output(self, name, width):
        """ Add a new output port to the module.

        Args:
            name : Name of the port
            width: Width of the port

        Returns: New port instance
        """
        return self.add_port(name, PortDirection.OUTPUT, width)

    def add_inout(self, name, width):
        """ Add a new bidirectional port to the module.

        Args:
            name : Name of the port
            width: Width of the port

        Returns: New port instance
        """
        return self.add_port(name, PortDirection.INOUT, width)

    def add_child(self, instance):
        """ Add another Module instance as a child.

        Args:
            instance: Module instance
        """
        assert isinstance(instance, Module) or isinstance(instance, Gate)
        assert instance.name not in self.children
        instance.parent              = self
        self.children[instance.name] = instance

    def base_copy(self):
        """ Copy the base container

        Returns: Instance of Module, or inherited class
        """
        return Module(self.name, self.type)

    def copy(self):
        """ Create a copy of this module and its children.

        Returns: Instance of Module, populated as a copy
        """
        # Setup the boundary
        new = self.base_copy()
        for port in self.inputs : new.add_input (port.name, port.width)
        for port in self.outputs: new.add_output(port.name, port.width)
        for port in self.inouts : new.add_inout (port.name, port.width)
        # Create copies of all child nodes
        for child in self.children.values():
            n_child = child.copy()
            new.add_child(n_child)
            if isinstance(child, Gate):
                for idx, bit in enumerate(child.inputs):
                    if not isinstance(bit, Constant): continue
                    n_child.inputs.append(Constant(bit.value))
                    n_child.inputs[-1].add_target(n_child)
            elif isinstance(child, Module):
                for port in child.inputs:
                    for bit in port.bits:
                        if not isinstance(bit.driver, Constant): continue
                        n_port       = n_child.ports[port.name]
                        n_bit        = n_port[bit.index]
                        n_bit.driver = Constant(bit.driver.value)
                        n_bit.driver.add_target(n_bit)
        # Construct primary input connectivity
        for port in self.inputs:
            n_port = new.ports[port.name]
            for bit in port.bits:
                n_bit = n_port[bit.index]
                for target in bit.targets:
                    if isinstance(target, Gate):
                        n_target = new.children[target.name]
                        n_bit.add_target(n_target)
                        n_target.inputs.append(n_bit)
                    elif isinstance(target, PortBit):
                        t_port   = target.port
                        t_parent = t_port.parent
                        # Find the matching target in the copy
                        n_tgt_parent = new.children[t_parent.name]
                        n_tgt_port   = n_tgt_parent.ports[t_port.name]
                        n_tgt_bit    = n_tgt_port[target.index]
                        # Create the connection
                        n_bit.add_target(n_tgt_bit)
                        n_tgt_bit.driver = n_bit
                    else:
                        raise Exception(f"Unexpected target {target}")
        # Construct child output connectivity
        for key, child in self.children.items():
            n_child = new.children[key]
            if isinstance(child, Gate):
                for target in child.outputs:
                    if isinstance(target, Gate):
                        n_target = new.children[target.name]
                        n_child.outputs.append(n_target)
                        n_target.inputs.append(n_child)
                    elif isinstance(target, PortBit):
                        t_port       = target.port
                        t_parent     = t_port.parent
                        n_tgt_parent = new.children.get(t_parent.name, new)
                        n_tgt_port   = n_tgt_parent.ports[t_port.name]
                        n_tgt_bit    = n_tgt_port[target.index]
                        n_child.outputs.append(n_tgt_bit)
                        n_tgt_bit.driver = n_child
                    else:
                        raise Exception(f"Unknown target {target}")
            elif isinstance(child, Module):
                for port in child.outputs:
                    n_port = n_child.ports[port.name]
                    for bit in port.bits:
                        n_bit = n_port[bit.index]
                        for target in bit.targets:
                            if isinstance(target, Gate):
                                n_target = new.children[target.name]
                                n_bit.add_target(n_target)
                                n_target.inputs.append(n_bit)
                            elif isinstance(target, PortBit):
                                t_port       = target.port
                                t_parent     = t_port.parent
                                n_tgt_parent = new.children.get(t_parent.name, new)
                                n_tgt_port   = n_tgt_parent.ports[t_port.name]
                                n_tgt_bit    = n_tgt_port[target.index]
                                n_bit.add_target(n_tgt_bit)
                                n_tgt_bit.driver = n_bit
                            else:
                                raise Exception(f"Unknown target {target}")
            else:
                raise Exception(f"Unknown child {child}")
        # Return the copy
        return new
