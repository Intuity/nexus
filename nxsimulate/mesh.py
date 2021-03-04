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
from .element import Element
from .network import Network

class Mesh(Base):
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
        assert isinstance(rows,    int)
        assert isinstance(columns, int)
        super().__init__(env, "Mesh")
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
