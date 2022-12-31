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

from orderedset import OrderedSet

class Grouping:

    GROUP_ID = 0

    def __init__(self, target, src_ports, tgt_ports, src_flops, gates):
        # Assign a unique ID
        self.id            = f"G{Grouping.GROUP_ID:03X}"
        Grouping.GROUP_ID += 1
        # Capture arguments
        self.target    = target
        self.src_ports = list(OrderedSet(src_ports))
        self.src_flops = list(OrderedSet(src_flops))
        self.tgt_ports = list(OrderedSet(tgt_ports))
        self.gates     = list(OrderedSet(gates))
        self.drives_to = OrderedSet()
        self.driven_by = OrderedSet()
        self.partition = None

    @property
    def complexity(self):
        return len(self.gates)
