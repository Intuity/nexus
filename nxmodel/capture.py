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
from .message import SignalState
from .node import OutputState

class Capture(Base):
    """ Captures signal state outputs from the mesh """

    def __init__(self, env, mesh, columns, lookup, debug=False):
        """ Initialise the Capture instance.

        Args:
            env    : SimPy environment
            mesh   : Pointer to the mesh
            columns: Number of columns in the mesh (number of inbound pipes)
            lookup : Dictionary to lookup output port names
            debug  : Log end of cycle summaries for every node (default: False)
        """
        super().__init__(env)
        self.mesh      = mesh
        self.inbound   = [None] * columns
        self.rx_loop   = self.env.process(self.capture())
        self.received  = []
        self.snapshots = []
        self.ticks     = 0
        self.lookup    = lookup
        self.debug_log = debug

    def write_to_vcd(self, vcd_path):
        """ Write all captured snapshots to a VCD file.

        Args:
            vcd_path: The path to the VCD file to write
        """
        def sig_name(row, col, pos):
            key = f"R{row}C{col}I{pos}"
            return self.lookup.get(key, key).replace("[", "_").replace("]", "_").replace(".", "_")
        with open(vcd_path, "w") as fh:
            with VCDWriter(fh, timescale="1 ns", date="today") as vcd:
                # Record the cycle
                cycle = vcd.register_var("tb", "cycle", "integer", size=32)
                # Register all outputs
                signals = {}
                for row, col, pos in set(sum([
                    list(x.keys()) for _, x, _, _ in self.snapshots
                ], [])):
                    signals[row, col, pos] = vcd.register_var(
                        "tb.dut", sig_name(row, col, pos), "integer", size=1
                    )
                # Register all node I/Os
                nodes = {}
                for node in self.mesh.all_nodes:
                    row, col = node.position
                    for idx in range(len(node.input_state)):
                        nodes[row, col, idx, "I"] = vcd.register_var(
                            f"tb.dut.mesh.row_{row}.col_{col}",
                            f"input_{idx}", "integer", size=1,
                        )
                    for idx in range(len(node.output_state)):
                        nodes[row, col, idx, "O"] = vcd.register_var(
                            f"tb.dut.mesh.row_{row}.col_{col}",
                            f"output_{idx}", "integer", size=1,
                        )
                # Write an initial state for all signals
                for sig in signals.values(): vcd.change(sig, 0, 0)
                # Convert all snapshots into VCD entries
                for time, (_, snapshot, node_inputs, node_outputs) in enumerate(
                    self.snapshots
                ):
                    vcd.change(cycle, time, time)
                    # Record output signals
                    for key, value in snapshot.items():
                        vcd.change(signals[key], time, value)
                    # Record node state
                    for (row, col), state in node_inputs.items():
                        for idx, value in enumerate(state):
                            vcd.change(nodes[row, col, idx, "I"], time, value)
                    for (row, col), state in node_outputs.items():
                        for idx, value in enumerate(state):
                            vcd.change(
                                nodes[row, col, idx, "O"], time,
                                value == OutputState.HIGH,
                            )

    def tick(self):
        # Increment tick counter
        self.ticks += 1
        # Summarise final output states from this tick
        snapshot = {}
        while self.received:
            item = self.received.pop(0)
            snapshot[item.src_row, item.src_col, item.src_pos] = item.src_val
        # Snapshot all node inputs and outputs
        node_inputs, node_outputs = {}, {}
        for node in self.mesh.all_nodes:
            node_inputs[node.position]  = node.input_state
            node_outputs[node.position] = node.output_state
        # Debug logging
        if self.debug_log:
            for row, row_entries in enumerate(self.mesh.nodes):
                for col, node in enumerate(row_entries):
                    i_curr = sum([
                        ((1 if y else 0) << x) for x, y in enumerate(node.input_state)
                    ])
                    i_next = sum([
                        ((1 if y else 0) << x) for x, y in enumerate(node.next_input_state)
                    ])
                    o_curr = sum([
                        ((1 if y else 0) << x) for x, y in enumerate(node.output_state)
                    ])
                    self.info(
                        f"[{self.ticks-1:04d}] {row:2d}, {col:2d} - IC: {i_curr:08b}, "
                        f"IN: {i_next:08b}, OC: {o_curr:08b} - Δ: {i_curr != i_next}"
                    )
        # Log and store snapshot
        self.info(f"Captured {len(snapshot)} outputs from tick {self.ticks-1}")
        self.snapshots.append((self.env.now, snapshot, node_inputs, node_outputs))

    def capture(self):
        """ Indefinite capture loop - observes signal state messages """
        while True:
            # Allow a cycle to elapse
            yield self.env.timeout(1)
            # Check all pipes
            for pipe in self.inbound:
                # Skip unattached pipes
                if pipe == None: continue
                # Skip empty pipes
                if pipe.idle: continue
                # Pop the next entry
                msg = yield self.env.process(pipe.pop())
                assert isinstance(msg, SignalState)
                self.debug(f"Captured output message {len(self.received)}")
                self.received.append(msg)
