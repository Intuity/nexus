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

import simpy

from .base import Base
from .pipe import Pipe
from .message import SignalState

class Capture(Base):
    """ Captures signal state outputs from the mesh """

    def __init__(self, env, columns):
        """ Initialise the Capture instance.

        Args:
            env    : SimPy environment
            columns: Number of columns in the mesh (number of inbound pipes)
        """
        super().__init__(env)
        self.inbound  = [None] * columns
        self.rx_loop  = self.env.process(self.capture())
        self.received = []

    def capture(self):
        """ Indefinite capture loop - observes signal state messages """
        while True:
            # Allow a cycle to elapse
            yield self.env.timeout(1)
            # Check all pipes
            for pipe in self.inbound:
                # Skip unattached pipes
                if not pipe: continue
                # Skip empty pipes
                if pipe.idle: continue
                # Pop the next entry
                msg = yield self.env.process(pipe.pop())
                assert isinstance(msg, SignalState)
                self.debug(f"Captured output message {len(self.received)}")
                self.received.append(msg)
