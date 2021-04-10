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

import simpy
from vcd import VCDWriter

from .base import Base
from .pipe import Pipe
from .message import SignalState

class Capture(Base):
    """ Captures signal state outputs from the mesh """

    def __init__(self, env, columns):
        """ Initialise the Capture instance.

        Args:
            env    : SimPy environment
            columns: Number of columns in the mesh (number of inbound pipes)
        """
        super().__init__(env)
        self.inbound   = [None] * columns
        self.rx_loop   = self.env.process(self.capture())
        self.received  = []
        self.snapshots = []

    def write_to_vcd(self, vcd_path):
        """ Write all captured snapshots to a VCD file.

        Args:
            vcd_path: The path to the VCD file to write
        """
        def key_name(key): return ", ".join([str(x) for x in key])
        with open(vcd_path, "w") as fh:
            with VCDWriter(fh, timescale="1 ns", date="today") as vcd:
                # Register all signals
                cycle   = vcd.register_var("tb", "cycle", "integer", size=32)
                signals = {}
                for key in set(sum([list(x.keys()) for _, x in self.snapshots], [])):
                    signals[key] = vcd.register_var(
                        "tb.dut", key_name(key), "integer", size=1
                    )
                # Convert all snapshots into VCD entries
                for time, (_, snapshot) in enumerate(self.snapshots):
                    vcd.change(cycle, time, time)
                    for key, value in snapshot:
                        vcd.change(signals[key], time, value)

    def tick(self):
        snapshot = {}
        while self.received:
            item = self.received.pop(0)
            snapshot[item.src_row, item.src_col, item.src_pos] = item.src_val
        self.snapshots.append((self.env.now, snapshot))

    def capture(self):
        """ Indefinite capture loop - observes signal state messages """
        while True:
            # Allow a cycle to elapse
            yield self.env.timeout(1)
            # Check all pipes
            for pipe in self.inbound:
                # Skip unattached pipes
                if not pipe: continue
                # Skip empty pipes
                if pipe.idle: continue
                # Pop the next entry
                msg = yield self.env.process(pipe.pop())
                assert isinstance(msg, SignalState)
                self.debug(f"Captured output message {len(self.received)}")
                self.received.append(msg)