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

from .port import Port, PortDirection

class Module:
    """ Represents a module in the hierarchy """

    def __init__(self, name, type):
        """ Initialise the Module instance.

        Args:
            name: Name of the module
            type: Type of the module
        """
        assert isinstance(name, str)
        assert isinstance(type, str)
        self.name     = name
        self.type     = type
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
        assert isinstance(instance, Module)
        assert instance.name not in self.children
        self.children[instance.name] = instance
