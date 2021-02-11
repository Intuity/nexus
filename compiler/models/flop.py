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

class Flop:
    """ Represents a flop in the design """

    def __init__(self, clock, reset, input, output, output_inv):
        """ Initialise the Flop instance.

        Args:
            clock     : Clock signal
            reset     : Reset signal
            input     : Input to the flop (D)
            output    : Output from the flop (Q)
            output_inv: Inverted output from the flop (QN)
        """
        self.clock      = clock
        self.reset      = reset
        self.input      = input
        self.output     = output
        self.output_inv = output_inv
