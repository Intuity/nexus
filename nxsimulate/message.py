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

from .base import Base

class Message(Base):
    """ Base class for a message """

    NEXT_ID = 0

    def __init__(self, env, data, initiator):
        """ Initialise Message instance.

        Args:
            env      : SimPy environment
            data     : Data to carry
            initiator: Where the message was sent from
        """
        self.id    = Message.issue_id()
        super().__init__(env, f"Message {self.id:05d}")
        self.data  = data
        self.chain = [(self.env.now, initiator)]

    @classmethod
    def issue_id(cls):
        the_id       = cls.NEXT_ID
        cls.NEXT_ID += 1
        return the_id

    def append_to_chain(self, node):
        self.chain.append((self.env.now, node))
