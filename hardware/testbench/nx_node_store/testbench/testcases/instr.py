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

from random import randint

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.instr.store import InstrStore
from drivers.instr.fetch import InstrFetch

from ..testbench import testcase

async def populate(dut, entries):
    """ Populate the instruction store with a given number of entries.

    Args:
        dut    : Pointer to the DUT
        entries: Total number of entries to populate

    Returns: Tuple of entries loaded for core 0 and for core 1
    """
    # Determine the instruction width
    instr_width = max(dut.store.intf.data._range)-min(dut.store.intf.data._range)+1

    # Load instructions randomly
    loaded = []
    for _ in range(entries):
        # Generate a random instruction
        instr = randint(0, (1 << instr_width) - 1)
        # Feed to one processor or the other
        dut.store.append(InstrStore(instr))
        loaded.append(instr)

    # Wait until all instructions have been loaded
    while dut.store._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Return tuple
    return loaded

@testcase()
async def load_instr(dut):
    """ Load random instructions and check they were stored correctly """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Check that the counter is at 0
    dut.info("Check that counter starts at 0")
    assert dut.populated == 0, "Populated count is not zero"

    # Determine the address bus width
    addr_width = max(dut.fetch.intf.addr._range)-min(dut.fetch.intf.addr._range)+1

    # Populate the instruction store
    loaded = await populate(dut, randint(100, (1 << addr_width) - 1))

    # Check the counters
    assert dut.populated == len(loaded), \
        f"Populated {len(dut.populated)}, expected {len(loaded)}"

    # Check the RAM state
    for addr, instr in enumerate(loaded):
        entry = dut.dut.dut.ram.memory[addr]
        assert entry.value.is_resolvable, f"Row {addr} could not resolve {entry}"
        assert int(entry) == instr, f"Row {addr} expected 0x{instr:08X} got 0x{entry:08X}"

@testcase()
async def fetch_instr(dut):
    """ Fetch instructions for from the store """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Populate the instruction store
    loaded = await populate(dut, 256)

    # Queue many transactions to fetch instructions
    launched = []
    for _ in range(1000):
        # Choose a random instruction to fetch
        instr_idx = randint(0, len(loaded)-1)
        instr     = loaded[instr_idx]

        # Perform a fetch
        fetch = InstrFetch(instr_idx)
        dut.fetch.append(fetch)

        # Track the operation and expected result
        launched.append((fetch, instr_idx, instr))

    # Continue to load instructions to create pressure
    cocotb.fork(populate(dut, 255))

    # Wait for each driver to complete
    while dut.fetch._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check each fetch
    for fetch, instr_idx, instr in launched:
        assert fetch.address == instr_idx, \
            f"Address mismatch 0x{fetch.address:X} != 0x{instr_idx:X}"
        assert fetch.data == instr, \
            f"Data mismatch 0x{fetch.data:X} != 0x{instr:X}"
