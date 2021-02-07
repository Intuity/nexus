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
