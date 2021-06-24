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
    """ Load instructions into every node via messages """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine parameters
    num_rows = int(dut.dut.dut.ROWS)
    num_cols = int(dut.dut.dut.COLUMNS)

    # Load a random number of instructions into every node
    loaded  = [[[ [], [] ] for _ in range(num_cols)] for _ in range(num_rows)]
    counter = 0
    for row in range(num_rows):
        for col in range(num_cols):
            for _ in range(randint(50, 200)):
                core  = choice((0, 1))
                instr = randint(0, (1 << 15) - 1)
                dut.inbound.append(build_load_instr(0, row, col, 0, core, instr))
                loaded[row][col][core].append(instr)
                counter += 1

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {counter} loads")
    while dut.inbound._sendQ: await RisingEdge(dut.clk)
    while dut.inbound.intf.valid == 1: await RisingEdge(dut.clk)

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            node   = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            core_0 = int(node.instr_store.core_0_populated_o)
            core_1 = int(node.instr_store.core_1_populated_o)
            assert core_0 == len(loaded[row][col][0]), \
                f"{row}, {col}: Expected {len(loaded[0])}, got {core_0}"
            assert core_1 == len(loaded[row][col][1]), \
                f"{row}, {col}: Expected {len(loaded[1])}, got {core_1}"

    # Check the loaded instructions
    for row in range(num_rows):
        for col in range(num_cols):
            node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            for core_idx, instrs in enumerate(loaded[row][col]):
                for op_idx, op in enumerate(instrs):
                    got = int(node.instr_store.ram.memory[op_idx+(core_idx*512)])
                    assert got == op, \
                        f"{row}, {col}: C{core_idx} O{op_idx} - exp {hex(op)}, got {hex(got)}"
