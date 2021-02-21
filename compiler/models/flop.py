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

    def __init__(self, name, clock, reset, input, output, output_inv=None):
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
        assert isinstance(clock,      Port)
        assert isinstance(reset,      Port)
        assert isinstance(input,      Port)
        assert isinstance(output,     Port)
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
