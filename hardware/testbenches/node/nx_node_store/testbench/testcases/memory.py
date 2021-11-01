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

from random import randint, random

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.memory.common import MemoryTransaction

from ..testbench import testcase

@testcase()
async def load(dut):
    """ Write entries in a random order """
    # Reset the DUT
    await dut.reset()

    # Determine shape of the memory
    ram_addr_w = int(dut.dut.u_dut.RAM_ADDR_W)
    ram_data_w = int(dut.dut.u_dut.RAM_DATA_W)
    ram_length = 1 << ram_addr_w

    # Write to the memory in a random order
    dut.info("Writing entries in a random order")
    state = {}
    for addr in sorted(range(ram_length), key=lambda _: random()):
        state[addr] = randint(0, (1 << ram_data_w) - 1)
        dut.load.append(MemoryTransaction(addr=addr, wr_data=state[addr], wr_en=True))

    # Wait for the driver to go idle
    dut.info("Waiting for DUT to go idle")
    await dut.load.idle()
    await ClockCycles(dut.clk, 10)

    # Backdoor check entries
    dut.info("Checking entries in RAM")
    for addr in range(ram_length):
        ram_data = int(dut.dut.u_dut.u_ram.memory[addr])
        assert ram_data == state[addr], \
            f"RAM mismatch at 0x{addr:08X}: 0x{ram_data:08X} != 0x{state[addr]:08X}"

@testcase()
async def read(dut):
    """ Write entries in a random order """
    # Reset the DUT
    await dut.reset()

    # Determine shape of the memory
    ram_addr_w = int(dut.dut.u_dut.RAM_ADDR_W)
    ram_data_w = int(dut.dut.u_dut.RAM_DATA_W)
    ram_length = 1 << ram_addr_w

    # Write to the memory in a random order
    dut.info("Writing entries in a random order")
    state = {}
    for addr in sorted(range(ram_length), key=lambda _: random()):
        state[addr] = randint(0, (1 << ram_data_w) - 1)
        dut.load.append(MemoryTransaction(addr=addr, wr_data=state[addr], wr_en=True))

    # Wait for the driver to go idle
    dut.info("Waiting for DUT to go idle")
    await dut.load.idle()
    # Launch reads of all entries via port A
    dut.info("Reading all entries via port A")
    rd_a_trans = []
    for addr in sorted(range(ram_length), key=lambda _: random()):
        rd_a_trans.append(MemoryTransaction(addr=addr, rd_en=True))
        dut.rd_a.append(rd_a_trans[-1])

    # Launch reads of all entries via port B
    dut.info("Reading all entries via port B")
    rd_b_trans = []
    for addr in sorted(range(ram_length), key=lambda _: random()):
        rd_b_trans.append(MemoryTransaction(addr=addr, rd_en=True))
        dut.rd_b.append(rd_b_trans[-1])

    # Wait for both read ports to go idle
    dut.info("Waiting for ports A & B to go idle")
    await dut.rd_a.idle()
    await dut.rd_b.idle()

    # Check every read from port A
    dut.info("Checking all port A transactions")
    for tran in rd_a_trans:
        assert tran.rd_data == state[tran.addr], \
            f"Read mismatch at 0x{tran.addr:08X}: 0x{tran.rd_data:08X} != " \
            f"0x{state[tran.addr]:08X}"

    # Check every read from port B
    dut.info("Checking all port B transactions")
    for tran in rd_b_trans:
        assert tran.rd_data == state[tran.addr], \
            f"Read mismatch at 0x{tran.addr:08X}: 0x{tran.rd_data:08X} != " \
            f"0x{state[tran.addr]:08X}"

@testcase()
async def read_and_write(dut):
    """ Perform continuous reads and writes to exercise stall """
    # Reset the DUT
    await dut.reset()

    # Determine shape of the memory
    ram_addr_w = int(dut.dut.u_dut.RAM_ADDR_W)
    ram_data_w = int(dut.dut.u_dut.RAM_DATA_W)
    ram_length = 1 << ram_addr_w

    # Write to the memory in a random order
    dut.info("Writing entries in a random order")
    state = {}
    for addr in sorted(range(ram_length), key=lambda _: random()):
        state[addr] = randint(0, (1 << ram_data_w) - 1)
        dut.load.append(MemoryTransaction(addr=addr, wr_data=state[addr], wr_en=True))

    # Wait for RAM to go idle
    await dut.load.idle()

    # Fork a thread running continuous write transactions to the lower half
    async def do_writes():
        while True:
            addr        = randint(0, (ram_length // 2) - 1)
            state[addr] = randint(0, (1 << ram_data_w) - 1)
            dut.load.append(MemoryTransaction(
                addr=addr, wr_data=state[addr], wr_en=True,
            ))
            await dut.load.idle()
    wr_thread = cocotb.fork(do_writes())

    # Fork threads to perform random reads from the upper half
    async def do_reads(intf, count=1000):
        for _ in range(count):
            tran = MemoryTransaction(
                addr =randint((ram_length // 2), ram_length - 1),
                rd_en=True,
            )
            intf.append(tran)
            await intf.idle()
            await RisingEdge(dut.clk)
            assert tran.rd_data == state[tran.addr], \
                f"Read mismatch 0x{tran.addr:08X} - 0x{tran.rd_data:08X} != " \
                f"0x{state[tran.addr]:08X}"

    rd_a_thread = cocotb.fork(do_reads(dut.rd_a, 1000))
    rd_b_thread = cocotb.fork(do_reads(dut.rd_b, 1000))

    # Wait for both threads to stop
    dut.info("Waiting for read threads to complete")
    await rd_a_thread.join()
    await rd_b_thread.join()

    # Kill the write thread
    dut.info("Killing write thread")
    wr_thread.kill()
    wr_thread = None
