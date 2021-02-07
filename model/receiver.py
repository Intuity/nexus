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
from .element import Element
from .network import Network, Pipe
from .message import Message

class Receiver(Base):
    """ Receiver for messages exiting the network """

    def __init__(self, env, inbound):
        """ Initialise the Receiver instance.

        Args:
            env    : SimPy environment
            inbound: The inbound port to receive data through
        """
        assert isinstance(inbound, Pipe)
        super().__init__(env, "Receiver")
        self.inbound  = inbound
        self.received = []
        self.action   = self.env.process(self.run())

    def run(self):
        """ Pickup messages from the inbound port """
        while True:
            # Wait for a message
            msg = yield self.env.process(self.inbound.pop())
            # Collect the message
            self.received.append((self.env.now, msg))
            # Log message received
            self.info(f"Message {msg.id:04d} - 0x{msg.data:08X}")
            for time, step in msg.chain:
                if isinstance(step, Element):
                    self.debug(f" - {step.row:4d}, {step.col:4d} @ {time:4d}")
                else:
                    self.debug(f" - {type(step).__name__} @ {time:4d}")
