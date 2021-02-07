from enum import IntEnum
from random import randint, choice, random

import simpy

from .network import Network
from .message import Message

class TxMode(IntEnum):
    RANDOM = 0 # Send random messages on each step
    UNIQUE = 1 # Send one message to every target on each step

class Transitter:
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
        assert isinstance(env,      simpy.Environment)
        assert isinstance(outbound, Network)
        assert isinstance(max_send, int)
        assert isinstance(bursts,   tuple)
        assert mode in TxMode
        self.env      = env
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
            print(
                f"[TX {self.sent[-1].id:04d}] Data 0x{self.sent[-1].data:08X} "
                f"@ {self.env.now}"
            )
        while (self.max_send <= 0) or (len(self.sent) < self.max_send):
            if self.mode == TxMode.RANDOM:
                for _ in range(min(
                    self.max_send - len(self.sent),
                    randint(self.bursts[0], self.bursts[1])
                )):
                    yield self.env.process(do_tx(
                        choice(range(self.outbound.num_targets)),
                        randint(0, (1 << 32) - 1)
                    ))
            elif self.mode == TxMode.UNIQUE:
                for tgt in range(self.outbound.num_targets):
                    yield self.env.process(do_tx(tgt, randint(0, (1 << 32) - 1)))
            # Wait for a cycle
            yield self.env.timeout(1)
