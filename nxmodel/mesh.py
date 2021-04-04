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
from .node import Node, Direction

class Mesh(Base):
    """ A mesh constructed of nodes and networks """

    def __init__(self, env, rows, columns, nd_prms=None):
        """ Initialise a Mesh instance.

        Args:
            env    : SimPy environment
            rows   : Number of rows in the mesh
            columns: Number of columns in the mesh
            nd_prms: Common parameters to all nodes
        """
        assert isinstance(rows,    int)
        assert isinstance(columns, int)
        assert nd_prms == None or isinstance(nd_prms, dict)
        super().__init__(env)
        # Ensure node parameters are a dictionary (to allow expansion)
        nd_prms = nd_prms if isinstance(nd_prms, dict) else {}
        # Create all of the nodes
        self.nodes = [
            [Node(env, r, c, **nd_prms) for c in range(columns)] for r in range(rows)
        ]
        # Link all of the pipes between nodes
        for row, columns in enumerate(self.nodes):
            for column, node in enumerate(columns):
                # Find the adjacent nodes to east and south
                # NOTE: Build connectivity always in these two directions to
                #       skip linking nodes that have already been handled
                to_east  = self.nodes[row][column+1] if column < (self.columns - 1) else None
                to_south = self.nodes[row+1][column] if row    < (self.rows    - 1) else None
                # Link the eastbound pipe
                if to_east:
                    assert not to_east.inbound[Direction.WEST]
                    assert not node.inbound[Direction.EAST]
                    to_east.inbound[Direction.WEST] = node.outbound[Direction.EAST]
                    node.inbound[Direction.EAST]    = to_east.outbound[Direction.WEST]
                # Link the southbound pipe
                if to_south:
                    assert not to_south.inbound[Direction.NORTH]
                    assert not node.inbound[Direction.SOUTH]
                    to_south.inbound[Direction.NORTH] = node.outbound[Direction.SOUTH]
                    node.inbound[Direction.SOUTH]     = to_south.outbound[Direction.NORTH]

    @property
    def rows(self): return len(self.nodes)
    @property
    def columns(self): return len(self.nodes[0])
