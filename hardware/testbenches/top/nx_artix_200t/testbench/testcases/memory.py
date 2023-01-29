# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from math import ceil
from random import choice, randint

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
from nxconstants import (ControlReqType, ControlRespType, ControlRequestMemory,
                         ControlRequestToMesh, ControlResponseMemory,
                         ControlResponseOutputs, NodeCommand, NodeSignal,
                         OUT_BITS_PER_MSG, TOP_MEM_ADDR_WIDTH, TOP_MEM_DATA_WIDTH,
                         TOP_MEM_STRB_WIDTH, TOP_MEM_COUNT)

from ..common import configure, to_bytes, trigger

async def memory(dut, index, en_wstrb):
    """ Read back parameters and status from the controller """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Pickup mesh parameters
    rows    = int(dut.u_dut.u_nexus.ROWS)
    columns = int(dut.u_dut.u_nexus.COLUMNS)
    nd_outs = int(dut.u_dut.u_nexus.OUTPUTS)
    mh_outs = columns * nd_outs

    # Get path to the memory instance
    u_memory = getattr(dut.u_dut.u_nexus.u_control, f"gen_top_mem[{index}]").u_memory

    # Get path to receiving node
    u_node = dut.u_dut.u_nexus.u_mesh.gen_rows[0].gen_columns[columns-TOP_MEM_COUNT+index].u_node

    # Initialise the memory
    dut.info(f"Initialising on-board memory {index}")
    state = {}
    for idx in range(1 << TOP_MEM_ADDR_WIDTH):
        state[idx] = randint(0, (1 << TOP_MEM_DATA_WIDTH) - 1)
        u_memory.memory[idx] <= state[idx]

    # Check that memories are disabled by default
    dut.info("Checking that memories are disabled by default")
    assert u_node.i_ext_inputs_en == 0

    # Enable basic memory access
    dut.info(f"Enabling memory access with strobes {'en' if en_wstrb else 'dis'}abled")
    await configure(
        dut,
        en_memory   =[(x == index) for x in range(TOP_MEM_COUNT)],
        en_mem_wstrb=[(en_wstrb and x == index) for x in range(TOP_MEM_COUNT)],
    )
    await RisingEdge(dut.clk)

    # Check that memory access is now enabled
    dut.info("Checking memory access now enabled")
    assert u_node.i_ext_inputs_en == 1, "Memory access has not been enabled"

    # Exercise backdoor memory access
    # NOTE: Write strobes are always enabled for backdoor accesses
    dut.info("Exercising backdoor memory accesses")
    for _ in range(100):
        # Queue up the request
        req         = ControlRequestMemory()
        req.command = ControlReqType.MEMORY
        req.memory  = index
        req.address = randint(0, (1 << TOP_MEM_ADDR_WIDTH) - 1)
        req.wr_n_rd = choice((0, 1))
        req.wr_data = randint(0, (1 << TOP_MEM_DATA_WIDTH) - 1)
        req.wr_strb = randint(0, (1 << TOP_MEM_STRB_WIDTH) - 1)
        dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req.pack(), 128)))
        # Update held state on writes
        if req.wr_n_rd:
            for idx in range(TOP_MEM_STRB_WIDTH):
                # Skip bytes where strobe is inactive
                if ((req.wr_strb >> idx) & 0x1) == 0: continue
                # Update byte
                mask               = 0xFF << (idx * 8)
                inv_mask           = ((1 << TOP_MEM_DATA_WIDTH) - 1) - mask
                state[req.address] = (req.wr_data & mask) | (state[req.address] & inv_mask)
        # Queue up a response on reads
        else:
            resp         = ControlResponseMemory()
            resp.format  = ControlRespType.MEMORY
            resp.rd_data = state[req.address]
            dut.expected.append(AXI4StreamTransaction(data=to_bytes(resp.pack(), 128)))

    # Wait for driver to return to idle
    dut.info("Waiting for requests to complete")
    await dut.inbound.idle()
    await ClockCycles(dut.clk, 10)

    # Check the memory state
    dut.info("Checking the memory state")
    for idx in range(1 << TOP_MEM_ADDR_WIDTH):
        exp = state[idx]
        got = int(u_memory.memory[idx])
        assert exp == got, f"@0x{idx:08X}: exp 0x{exp:08X}, got 0x{got:08X}"

    # Trigger the mesh
    dut.info("Triggering the mesh")
    await trigger(dut, active=1, cycles=101)

    # Wait for the trigger event
    dut.info("Waiting for the first trigger event")
    while dut.u_dut.u_nexus.u_mesh.i_trigger == 0: await RisingEdge(dut.clk)

    # Work out the output offset for this memory
    offset = index * sum((
        TOP_MEM_ADDR_WIDTH, TOP_MEM_DATA_WIDTH, TOP_MEM_STRB_WIDTH, 2
    ))

    # Calculate the positions of each port
    idx_addr    = mh_outs - offset - TOP_MEM_ADDR_WIDTH
    idx_wr_data = idx_addr - TOP_MEM_DATA_WIDTH
    idx_wr_en   = idx_wr_data - 1
    idx_rd_en   = idx_wr_en - 1
    idx_wr_strb = idx_rd_en - TOP_MEM_STRB_WIDTH

    # Exercise design memory access
    dut.info("Exercising design memory accesses")
    last_outs = []
    for cycle in range(100):
        # Decide on action to perform
        address = randint(0, (1 << TOP_MEM_ADDR_WIDTH) - 1)
        wr_n_rd = choice((0, 1))
        wr_data = randint(0, (1 << TOP_MEM_DATA_WIDTH) - 1)
        wr_strb = randint(0, (1 << TOP_MEM_STRB_WIDTH) - 1)
        # dut.info(
        #     f"@0x{address:08X} - WR: {wr_n_rd}, WD: 0x{wr_data:08X}, "
        #     f"ST: 0x{wr_strb:X}"
        # )
        # Generate the mesh outputs
        outputs = (
            (randint(0, (1 << offset) - 1) << (mh_outs - offset)) |
            (address                       << idx_addr          ) |
            (wr_data                       << idx_wr_data       ) |
            (wr_n_rd                       << idx_wr_en         ) |
            ((0 if wr_n_rd else 1)         << idx_rd_en         ) |
            (wr_strb                       << idx_wr_strb       ) |
            randint(0, (1 << idx_wr_strb) - 1)
        )
        # Emit signal update messages
        for idx in range(mh_outs):
            # Generate signal message
            msg                = NodeSignal()
            msg.header.row     = rows
            msg.header.column  = (idx // nd_outs)
            msg.header.command = NodeCommand.SIGNAL
            msg.is_seq         = 1
            msg.index          = (idx % nd_outs)
            msg.state          = (outputs >> idx) & 0x1
            # Queue control request
            req         = ControlRequestToMesh()
            req.command = ControlReqType.TO_MESH
            req.message = msg.pack()
            dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req.pack(), 128)))
        # Queue up the output responses
        last_outs = []
        for idx in range(ceil(mh_outs / OUT_BITS_PER_MSG)):
            resp         = ControlResponseOutputs()
            resp.format  = ControlRespType.OUTPUTS
            resp.stamp   = cycle
            resp.index   = idx
            resp.section = (
                (outputs >> (idx * OUT_BITS_PER_MSG)) & ((1 << OUT_BITS_PER_MSG) - 1)
            )
            dut.expected.append(AXI4StreamTransaction(data=to_bytes(resp.pack(), 128)))
            last_outs.append(resp)
        # Wait for the trigger event
        while dut.u_dut.u_nexus.u_mesh.i_trigger != 0: await RisingEdge(dut.clk)
        while dut.u_dut.u_nexus.u_mesh.i_trigger == 0: await RisingEdge(dut.clk)
        # For writes, check the memory state updated
        if wr_n_rd:
            for idx in range(TOP_MEM_STRB_WIDTH):
                # Skip bytes where strobe is inactive
                if en_wstrb and ((wr_strb >> idx) & 0x1) == 0: continue
                # Update byte
                mask           = 0xFF << (idx * 8)
                inv_mask       = ((1 << TOP_MEM_DATA_WIDTH) - 1) - mask
                state[address] = (wr_data & mask) | (state[address] & inv_mask)
            exp = state[address]
            got = int(u_memory.memory[address])
            assert exp == got, f"@0x{address:08X}: exp 0x{exp:08X}, got 0x{got:08X}"
        # For reads, check that the returned data is correct
        else:
            exp = state[address]
            got = int(u_node.i_ext_inputs)
            assert exp == got, f"@0x{address:08X}: exp 0x{exp:08X}, got 0x{got:08X}"

    # Repeat the final cycle's outputs (as an N+1 cycle is triggered)
    for msg in last_outs:
        msg.stamp += 1
        dut.expected.append(AXI4StreamTransaction(data=to_bytes(msg.pack(), 128)))

factory = TestFactory(memory)
factory.add_option("index", range(TOP_MEM_COUNT))
factory.add_option("en_wstrb", (True, False))
factory.generate_tests()
