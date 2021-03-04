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

from .module import Module
from .port import Port

class Flop(Module):
    """ Represents a flop in the design """

    def __init__(
        self, name, clock=None, reset=None, input=None, output=None,
        output_inv=None
    ):
        """ Initialise the Flop instance.

        Args:
            name      : Name of the flop instance
            clock     : Clock signal
            reset     : Reset signal
            input     : Input to the flop (D)
            output    : Output from the flop (Q)
            output_inv: Inverted output from the flop (QN)
        """
        super().__init__(name, "flop")
        assert isinstance(clock,      Port) or clock      == None
        assert isinstance(reset,      Port) or reset      == None
        assert isinstance(input,      Port) or input      == None
        assert isinstance(output,     Port) or output     == None
        assert isinstance(output_inv, Port) or output_inv == None
        self.clock      = clock
        self.reset      = reset
        self.input      = input
        self.output     = output
        self.output_inv = output_inv
        if self.clock     : self.add_raw_port(self.clock)
        if self.reset     : self.add_raw_port(self.reset)
        if self.input     : self.add_raw_port(self.input)
        if self.output    : self.add_raw_port(self.output)
        if self.output_inv: self.add_raw_port(self.output_inv)

    def base_copy(self):
        """ Copy the base Flop container.

        Returns: Instance of Flop
        """
        return Flop(self.name)

    def copy(self):
        """ Create a copy of this Flop.

        Returns: Instance of Flop, populated as a copy
        """
        # Use Module base class to form the copy
        new = super().copy()
        # Re-associate each of the port aliases
        new.clock      = new.ports[self.clock.name     ] if self.clock      else None
        new.reset      = new.ports[self.reset.name     ] if self.reset      else None
        new.input      = new.ports[self.input.name     ] if self.input      else None
        new.output     = new.ports[self.output.name    ] if self.output     else None
        new.output_inv = new.ports[self.output_inv.name] if self.output_inv else None
        # Return the copy
        return new
