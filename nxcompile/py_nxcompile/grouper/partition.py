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

class Partition:

    def __init__(self, index, limits, all_parts, tgt_flop_map):
        self.index        = index
        self.limits       = limits
        self.all_parts    = all_parts
        self.tgt_flop_map = tgt_flop_map
        self.groups       = []
        self.tgt_flops    = None
        self.src_flops    = None
        self.src_ports    = None
        self.tgt_ports    = None
        self.all_gates    = None

    @property
    def id(self):
        return f"P{self.index:03d}"

    def add_group(self, group):
        assert group not in self.groups
        self.groups.append(group)
        group.partition = self

    def remove_group(self, group):
        self.groups.remove(group)

    def aggregate(self):
        self.tgt_flops = set()
        self.src_flops = set()
        self.src_ports = set()
        self.tgt_ports = set()
        self.all_gates = set()
        for group in self.groups:
            self.tgt_flops.add(group.target)
            self.tgt_flop_map[group.target.name] = self
            self.src_flops = self.src_flops.union(set(group.src_flops))
            self.src_ports = self.src_ports.union(set(group.src_ports))
            self.tgt_ports = self.tgt_ports.union(set(group.tgt_ports))
            self.all_gates = self.all_gates.union(set(group.gates))

    @property
    def empty(self):
        return not any(self.usage().values())

    def usage(self):
        # For each source flop, identify if its in a different partition
        flop_inputs = len([x for x in self.src_flops if self.tgt_flop_map[x.name] is not self])
        # Build a full list of flops required by other partitions
        other_flops = sum([[x.name for x in y.src_flops] for y in self.all_parts if y is not self], [])
        # Count the total number of places each target flop needs to talk to
        flop_outputs = sum([other_flops.count(x.name) for x in self.tgt_flops])
        # Summarise requirements
        return {
            "inputs" : (flop_inputs + len(self.src_ports)),
            "outputs": (flop_outputs                     ),
            "gates"  : (len(self.all_gates)              ),
            "flops"  : (len(self.tgt_flops)              ),
        }

    def utilisation(self):
        required = self.usage()
        return { k: (required[k] / v) for k, v in self.limits.items() }

    def fits(self):
        required = self.usage()
        return { k: (required[k] <= v) for k, v in self.limits.items() }

    def report(self):
        req_str = ", ".join(f"{k[0].upper()}: {v:4d}" for k, v in self.usage().items())
        fit_str = ", ".join(f"{k[0].upper()}: {v:1d}" for k, v in self.fits().items())
        utl_str = ", ".join(f"{k[0].upper()}: {v*100:5.1f}%" for k, v in self.utilisation().items())
        fits    = all(self.fits().values())
        return (
            f"{self.id} {len(self.groups):4d} groups - Req: "
            + req_str + " - Fits? " + fit_str + " - Util: " + utl_str
            + " [" + ("   " if fits else "!!!") + "]"
        )

    def can_fit(self, *groups):
        # Build complete lists of flops, ports, and gates
        all_tgt_flops = self.tgt_flops.union({ x.target for x in groups })
        all_src_flops = self.src_flops.union(sum([x.src_flops for x in groups], []))
        all_src_ports = self.src_ports.union(sum([x.src_ports for x in groups], []))
        all_gates     = self.all_gates.union(sum([x.gates for x in groups], []))
        # For each source flop, identify if its in a different partition
        tgt_names   = [x.target.name for x in groups]
        flop_inputs = len([x for x in all_src_flops if self.tgt_flop_map[x.name] is not self and x.name not in tgt_names])
        # Build a full list of flops required by other partitions
        other_flops = []
        for other in self.all_parts:
            if other is self:
                continue
            part_src_flops = []
            for group in other.groups:
                if group in groups:
                    continue
                part_src_flops += [x.name for x in group.src_flops]
            other_flops += list(set(part_src_flops))
        # Count the total number of places each target flop needs to talk to
        flop_outputs = sum([other_flops.count(x.name) for x in all_tgt_flops])
        # Assemble the requirements
        required = {
            "inputs" : (flop_inputs + len(all_src_ports)),
            "outputs": (flop_outputs                    ),
            "gates"  : (len(all_gates)                  ),
            "flops"  : (len(all_tgt_flops)              ),
        }
        # Check for fit
        return all([(required[k] <= v) for k, v in self.limits.items()])

    def can_merge(self, other):
        return self.can_fit(*other.groups)
