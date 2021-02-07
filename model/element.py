from random import choice, randint

import simpy

from .base import Base
from .network import Network, Pipe
from .message import Message

class Element(Base):
    """ A single compute element in the network """

    def __init__(self, env, row, col, inbound, outbound):
        """ Initialise Element instance.

        Args:
            env    : SimPy environment
            row    : Row position in the mesh
            col    : Column position in the mesh
            inbound: Inbound pipe from network for receiving data
            outbound : Outbound pipe to network for transmitting data
        """
        assert isinstance(row,      int    )
        assert isinstance(col,      int    )
        assert isinstance(inbound,  Pipe   )
        assert isinstance(outbound, Network)
        super().__init__(env, f"Element {row:02d}, {col:02d}")
        self.row      = row
        self.col      = col
        self.inbound  = inbound
        self.outbound = outbound
        self.action   = self.env.process(self.run())
        # Track active and idle cycles
        self.active   = 0
        self.idle     = 0

    @property
    def utilisation(self):
        return (self.active / (self.idle + self.active)) * 100

    def run(self):
        """ Pickup messages from the inbound - transform and deliver to outbound """
        last_tx = 0
        while True:
            # Wait for message
            msg        = yield self.env.process(self.inbound.pop())
            start      = self.env.now
            self.idle += start - last_tx
            # Log message capture
            self.debug(f"Received message {msg.id}")
            # Sanity check
            assert isinstance(msg, Message)
            # Append this node to the chain
            msg.append_to_chain(self)
            # Delay for a cycle
            yield self.env.timeout(1)
            self.debug(f"Sending message {msg.id}")
            yield self.env.process(self.outbound.transmit(
                choice(range(self.outbound.num_targets)), msg
            ))
            # yield self.env.process(self.outbound.transmit(self.col, msg))
            last_tx      = self.env.now
            self.active += last_tx - start

