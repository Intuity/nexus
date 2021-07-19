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
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Load a random number of instructions into every node
    loaded  = [[[] for _ in range(num_cols)] for _ in range(num_rows)]
    counter = 0
    for row in range(num_rows):
        for col in range(num_cols):
            for _ in range(randint(10, 30)):
                instr = randint(0, (1 << 15) - 1)
                dut.mesh_inbound.append(build_load_instr(row, col, instr))
                loaded[row][col].append(instr)
                counter += 1

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {counter} loads")
    await dut.mesh_inbound.idle()

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            pop  = int(node.store.instr_count_o)
            assert pop == len(loaded[row][col]), \
                f"{row}, {col}: Expected {len(loaded[row][col])}, got {pop}"

    # Check the loaded instructions
    for row in range(num_rows):
        for col in range(num_cols):
            node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            for op_idx, op in enumerate(loaded[row][col]):
                got = int(node.store.ram.memory[op_idx])
                assert got == op, \
                    f"{row}, {col}: O{op_idx} - exp {hex(op)}, got {hex(got)}"
