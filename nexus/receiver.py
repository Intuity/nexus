import simpy

from .element import Element
from .network import Network, Pipe
from .message import Message

class Receiver:
    """ Receiver for messages exiting the network """

    def __init__(self, env, inbound):
        """ Initialise the Receiver instance.

        Args:
            env    : SimPy environment
            inbound: The inbound port to receive data through
        """
        assert isinstance(env,     simpy.Environment)
        assert isinstance(inbound, Pipe)
        self.env      = env
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
            print(f"[RX {msg.id:04d}] Data 0x{msg.data:08X} @ {self.env.now}")
            # for time, step in msg.chain:
            #     if isinstance(step, Element):
            #         print(f" - {step.row:4d}, {step.col:4d} @ {time:4d}")
            #     else:
            #         print(f" - {type(step).__name__} @ {time:4d}")
