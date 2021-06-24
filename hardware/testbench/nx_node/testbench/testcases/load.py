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

from cocotb.triggers import ClockCycles, RisingEdge

from nx_message import build_load_instr

from ..testbench import testcase

@testcase()
async def load(dut):
    """ Load instructions into a node via messages """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.info(f"Setting row to {row} & column to {col}")
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Select an inbound pipe
    inbound = choice(dut.inbound)

    # Load a random number of instructions
    loaded = [[] for _ in range(2)]
    for _ in range(randint(10, 500)):
        # Generate instruction
        core  = choice((0, 1))
        instr = randint(0, (1 << 15) - 1)
        inbound.append(build_load_instr(0, row, col, 0, core, instr))
        loaded[core].append(instr)

    # Wait for all inbound drivers to drain
    dut.info(f"Waiting for {sum([len(x) for x in loaded])} loads")
    for ib in dut.inbound:
        while ib._sendQ: await RisingEdge(dut.clk)
        while ib.intf.valid == 1: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the instruction counters
    assert dut.dut.dut.instr_store.core_0_populated_o == len(loaded[0]), \
        f"Expected {len(loaded[0])}, got {int(dut.dut.dut.instr_store.core_0_populated_o)}"
    assert dut.dut.dut.instr_store.core_1_populated_o == len(loaded[1]), \
        f"Expected {len(loaded[1])}, got {int(dut.dut.dut.instr_store.core_1_populated_o)}"

    # Check the loaded instructions
    for core_idx, instrs in enumerate(loaded):
        for op_idx, op in enumerate(instrs):
            got = int(dut.dut.dut.instr_store.ram.memory[op_idx+(core_idx*512)])
            assert got == op, f"C{core_idx} O{op_idx} - exp {hex(op)}, got {hex(got)}"
