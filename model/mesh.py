from .element import Element
from .network import Network

class Mesh:
    """ A mesh constructed of nodes and networks """

    # Positions in array for busy and idle counters
    STAT_BUSY = 0
    STAT_IDLE = 1

    # How many cycles until monitoring should time out
    IDLE_TIMEOUT = 20

    def __init__(self, env, rows, columns):
        """ Initialise a Mesh instance.

        Args:
            env    : SimPy environment
            rows   : Number of rows in the mesh
            columns: Number of columns in the mesh
        """
        self.env     = env
        self.rows    = rows
        self.columns = columns
        # Start with an initial network - this is the entrypoint
        self.networks  = [Network(self.env, delay=1, capacity=1)]
        # Build up a grid of elements
        self.elements = []
        for row in range(self.rows):
            # Create network and empty statistics
            self.networks.append(Network(self.env, 1, 1))
            # Create elements and empty statistics
            self.elements.append([])
            for col in range(self.columns):
                self.elements[-1].append(Element(
                    self.env,
                    row, col,
                    self.networks[-2].add_target(),
                    self.networks[-1],
                ))
        # Add a catch-all egress target to the final network
        self.egress = self.networks[-1].add_target(catchall=True, capacity=100)

    @property
    def ingress(self): return self.networks[0]
