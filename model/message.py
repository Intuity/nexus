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
