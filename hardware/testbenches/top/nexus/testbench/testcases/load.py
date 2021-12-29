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

from itertools import product
from random import randint

from cocotb.triggers import ClockCycles, RisingEdge

from nxconstants import ControlReqType, ControlRequest, NodeID

from drivers.stream.common import StreamTransaction
from node.load import load_data

from ..testbench import testcase

@testcase()
async def load(dut):
    """ Load random data into every node via messages """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine parameters
    num_rows   = int(dut.ROWS)
    num_cols   = int(dut.COLUMNS)
    ram_data_w = int(dut.RAM_DATA_W)
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Create a proxy for loading into the mesh
    class InboundProxy:
        def append(self, tran):
            req                 = ControlRequest()
            req.to_mesh.command = ControlReqType.TO_MESH
            req.to_mesh.message = tran.data
            dut.ctrl_in.append(StreamTransaction(req.pack()))
        async def idle(self):
            await dut.ctrl_in.idle()
    proxy = InboundProxy()

    # Load random data into every node
    loaded  = [[[] for _ in range(num_cols)] for _ in range(num_rows)]
    counter = 0
    for row in range(num_rows):
        for col in range(num_cols):
            loaded[row][col] = [
                randint(0, (1 << ram_data_w) - 1) for _ in range(randint(50, 100))
            ]
            load_data(
                inbound   =proxy,
                node_id   =NodeID(row=row, column=col),
                ram_data_w=ram_data_w,
                stream    =loaded[row][col]
            )
            counter += len(loaded[row][col])

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {counter} loads")
    await proxy.idle()

    # Wait for the idle flag to go high
    while dut.status.idle == 0: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the next load address for every node
    for row, col in product(range(num_rows), range(num_cols)):
        pop  = int(dut.nodes[row][col].u_decoder.load_address_q)
        assert pop == len(loaded[row][col]), \
            f"{row}, {col}: Expected {len(loaded[row][col])}, got {pop}"

    # Check the loaded data
    for row, col in product(range(num_rows), range(num_cols)):
        for op_idx, op in enumerate(loaded[row][col]):
            got = int(dut.nodes[row][col].u_store.u_ram.memory[op_idx])
            assert got == op, \
                f"{row}, {col}: O{op_idx} - exp {hex(op)}, got {hex(got)}"
