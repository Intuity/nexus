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

class Pipe(Base):
    """ Pipe with a delay """

    def __init__(self, env, delay, capacity):
        """ Initialise Pipe instance.

        Args:
            env     : SimPy environment
            network : Parent Network instance
            delay   : Propagation delay for the pipe
            capacity: Per-pipe capacity
        """
        # Setup base class
        super().__init__(env)
        # Capture delay and capacity
        assert isinstance(delay,    int)
        assert isinstance(capacity, int)
        self.delay    = delay
        self.capacity = capacity
        # Setup SimPy FIFOs
        self.in_store  = simpy.Store(env, capacity=capacity)
        self.out_store = simpy.Store(env, capacity=1)
        # Setup run loop
        self.action = env.process(self.run())
        # Initialise counters
        self.num_push   = 0
        self.num_pop    = 0
        self.first_push = 0
        self.last_pop   = 0
        # Initialise timestamps
        self.__idle   = 0
        self.__active = 0

    @property
    def idle(self):
        if self.num_push == self.num_pop:
            return self.__idle + (self.env.now - self.last_pop)
        else:
            return self.__idle

    @property
    def active(self):
        if self.num_push == self.num_pop:
            return self.__active
        else:
            return self.__active + (self.env.now - self.first_push)

    @property
    def utilisation(self):
        return (self.active / (self.idle + self.active)) * 100

    def push(self, msg):
        # If empty, record idle time
        if self.num_push == self.num_pop:
            self.__idle     += (self.env.now - self.last_pop)
            self.first_push  = self.env.now
        # Increment number of pushes
        self.num_push += 1
        # Push to the inbound store
        self.debug(f"Message {msg.id} pushed")
        yield self.in_store.put((self.env.now, msg))

    def pop(self):
        # Pop the next entry
        entry, msg = yield self.out_store.get()
        self.debug(f"Message {msg.id} popped")
        # Increment number of items popped
        self.num_pop += 1
        # If empty, record active time
        if self.num_pop == self.num_push:
            self.__active += (self.env.now - self.first_push)
            self.last_pop  = self.env.now
        return msg

    def run(self):
        last_put = 0
        while True:
            # Wait for a message on the inbound store
            entry, msg = yield self.in_store.get()
            # Delay for expected number of cycles
            if (self.env.now - entry) < self.delay:
                yield self.env.timeout(self.delay - (self.env.now - entry))
            # Deliver to the outbound store
            self.out_store.put((entry, msg))
