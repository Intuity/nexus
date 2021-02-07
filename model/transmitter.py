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

from enum import IntEnum
from random import randint, choice, random

import simpy

from .base import Base
from .network import Network
from .message import Message

class TxMode(IntEnum):
    RANDOM = 0 # Send random messages on each step
    UNIQUE = 1 # Send one message to every target on each step

class Transitter(Base):
    """ Transmit messages into the network """

    def __init__(
        self, env, outbound, max_send=0, bursts=(0, 5), mode=TxMode.RANDOM
    ):
        """ Initialise the Transmitter instance

        Args:
            env     : SimPy environment
            outbound: Outbound port to transmit messages on
            max_send: Maximum number of messages to send (default: 0 - infinite)
            bursts  : Number of messages to send per cycle (default: 0 min, 5 max)
        """
        assert isinstance(outbound, Network)
        assert isinstance(max_send, int)
        assert isinstance(bursts,   tuple)
        assert mode in TxMode
        super().__init__(env, "Transmitter")
        self.outbound = outbound
        self.action   = self.env.process(self.run())
        self.sent     = []
        self.max_send = max_send
        self.bursts   = bursts
        self.mode     = mode

    def run(self):
        """ Generate random messages and transmit them to random targets """
        def do_tx(tgt, data):
            self.sent.append(Message(self.env, data, self))
            yield self.env.process(self.outbound.transmit(tgt, self.sent[-1]))
            self.info(
                f"Message {self.sent[-1].id:04d} - 0x{self.sent[-1].data:08X}"
            )
        while (self.max_send <= 0) or (len(self.sent) < self.max_send):
            remain  = self.max_send - len(self.sent)
            num_tgt = self.outbound.num_targets
            order   = []
            # Generate random messages to any target any number of times
            if self.mode == TxMode.RANDOM:
                num_send  = min(remain, num_tgt, randint(self.bursts[0], self.bursts[1]))
                order    += [choice(range(num_tgt)) for _ in range(num_send)]
            # Generate one message per target per cycle in any order
            elif self.mode == TxMode.UNIQUE:
                num_send  = min(remain, num_tgt)
                order    += sorted(range(num_send), key=lambda _: random())[:num_send]
            # Send all of the messages
            for tgt in order:
                yield self.env.process(do_tx(tgt, randint(0, (1 << 32) - 1)))
            # Wait for a cycle
            yield self.env.timeout(1)
