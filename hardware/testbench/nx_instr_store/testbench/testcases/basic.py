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

from random import choice, randint

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.instr.store import InstrStore
from drivers.instr.fetch import InstrFetch
from nx_constants import Direction

from ..testbench import testcase

@testcase()
async def sanity(dut):
    """ Basic testcase """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Run for 100 clock cycles
    dut.info("Running for 100 clock cycles")
    await ClockCycles(dut.clk, 100)

    # All done!
    dut.info("Finished counting cycles")

async def populate(dut, entries):
    """ Populate the instruction store with a given number of entries.

    Args:
        dut    : Pointer to the DUT
        entries: Total number of entries to populate

    Returns: Tuple of entries loaded for core 0 and for core 1
    """
    # Determine the instruction width
    instr_width = max(dut.store.intf.data._range)-min(dut.store.intf.data._range)+1

    # Load instructions randomly to core 0 or core 1
    loaded = ([], [])
    for _ in range(entries):
        # Select a random core
        core = choice((0, 1))
        # Generate a random instruction
        instr = randint(0, (1 << instr_width) - 1)
        # Feed to one processor or the other
        dut.store.append(InstrStore(core, instr))
        loaded[core].append(instr)

    # Wait until all instructions have been loaded
    while dut.store._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Return tuple
    return loaded

@testcase()
async def load_instr(dut):
    """ Load random instructions for core 0 and core 1 """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Check that the populated counters are at 0
    dut.info("Check that populated counters start at 0")
    assert dut.populated[0] == 0, "Core 0 populated count is not zero"
    assert dut.populated[1] == 0, "Core 1 populated count is not zero"

    # Determine the address bus width
    addr_width = max(dut.core[0].intf.addr._range)-min(dut.core[0].intf.addr._range)+1

    # Populate the instruction store
    loaded = await populate(dut, randint(100, (1 << addr_width) - 1))

    # Check the counters
    assert dut.populated[0] == len(loaded[0]), \
        f"Core 0 populated {len(dut.populated[0])}, expected {len(loaded[0])}"
    assert dut.populated[1] == len(loaded[1]), \
        f"Core 0 populated {len(dut.populated[1])}, expected {len(loaded[1])}"

    # Check the RAM state
    for core, instrs in enumerate(loaded):
        for addr, instr in enumerate(instrs):
            entry = dut.dut.dut.ram.memory[addr + (core << addr_width)]
            assert entry.value.is_resolvable, \
                f"Core {core} row {addr} could not resolve {entry}"
            assert int(entry) == instr, \
                f"Core {core} row {addr} expected 0x{instr:08X} got 0x{entry:08X}"

@testcase()
async def fetch_instr(dut):
    """ Fetch instructions for each core from the store """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine the address bus width
    addr_width = max(dut.core[0].intf.addr._range)-min(dut.core[0].intf.addr._range)+1

    # Populate the instruction store
    loaded = await populate(dut, 256)

    # Queue many transactions to fetch instructions
    launched = []
    for _ in range(1000):
        # Select a random core
        core = choice(range(len(loaded)))

        # Choose a random instruction to fetch
        instr_idx = randint(0, len(loaded[core])-1)
        instr     = loaded[core][instr_idx]

        # Perform a fetch
        fetch = InstrFetch(instr_idx)
        dut.core[core].append(fetch)

        # Track the operation and expected result
        launched.append((fetch, instr_idx, instr))

    # Continue to load instructions to create pressure
    cocotb.fork(populate(dut, 255))

    # Wait for each driver to complete
    while dut.core[0]._sendQ: await RisingEdge(dut.clk)
    while dut.core[1]._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check each fetch
    for fetch, instr_idx, instr in launched:
        assert fetch.address == instr_idx, \
            f"Address mismatch 0x{fetch.address:X} != 0x{instr_idx:X}"
        assert fetch.data == instr, \
            f"Data mismatch 0x{fetch.data:X} != 0x{instr:X}"
