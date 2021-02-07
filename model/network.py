import simpy

from .base import Base

class Pipe(Base):
    """ Pipe with a delay """

    def __init__(self, env, network, pipe_id, delay, capacity):
        """ Initialise Pipe instance.

        Args:
            env     : SimPy environment
            network : Parent Network instance
            delay   : Propagation delay for the pipe
            capacity: Per-pipe capacity
        """
        assert isinstance(network,  Network)
        assert isinstance(pipe_id,  int)
        assert isinstance(delay,    int)
        assert isinstance(capacity, int)
        super().__init__(env, f"Net {network.id} Pipe {pipe_id}")
        self.pipe_id    = pipe_id
        self.network    = Network
        self.delay      = delay
        self.capacity   = capacity
        self.in_store   = simpy.Store(env, capacity=capacity)
        self.out_store  = simpy.Store(env, capacity=1)
        self.action     = env.process(self.run())
        self.__idle     = 0
        self.__active   = 0
        self.num_push   = 0
        self.num_pop    = 0
        self.first_push = 0
        self.last_pop   = 0

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

class Network(Base):
    """ Multi-in-multi-out network. """

    NEXT_ID = 0

    def __init__(self, env, delay, capacity):
        """ Initialise Network instance.

        Args:
            env     : SimPy environment
            delay   : Propagation delay on each pipe
            capacity: Per-pipe capacity
        """
        assert isinstance(delay,    int)
        assert isinstance(capacity, int)
        self.id        = Network.issue_id()
        super().__init__(env, f"Network {self.id:2d}")
        self.delay     = delay
        self.capacity  = capacity
        self.in_flight = []
        self.pipes     = []
        self.catchall  = None

    @classmethod
    def issue_id(cls):
        the_id       = cls.NEXT_ID
        cls.NEXT_ID += 1
        return the_id

    @property
    def idle(self): return sum([x.idle for x in self.pipes])

    @property
    def active(self): return sum([x.active for x in self.pipes])

    @property
    def utilisation(self):
        return (self.active / (self.active + self.idle)) * 100

    @property
    def num_targets(self): return len(self.pipes)

    def transmit(self, target, message):
        assert isinstance(target, int)
        oob = (target < 0) or (target >= len(self.pipes))
        if oob and not self.catchall: raise Exception(f"Bad target: {target}")
        target = self.catchall if oob else self.pipes[target]
        yield self.env.process(target.push(message))

    def add_target(self, catchall=False, capacity=None):
        if capacity == None: capacity = self.capacity
        self.pipes.append(Pipe(self.env, self, len(self.pipes), 1, capacity))
        if catchall: self.catchall = self.pipes[-1]
        return self.pipes[-1]

