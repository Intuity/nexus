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

import nxconstants
from nxconstants import Instruction, Operation, NodeLoadInstr, NodeCommand

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
    loaded = []
    for _ in range(randint(10, 500)):
        msg = NodeLoadInstr()
        msg.header.row     = row
        msg.header.column  = col
        msg.header.command = NodeCommand.LOAD_INSTR
        msg.instr.opcode   = choice(list(Operation))
        msg.instr.src_a    = randint(0, nxconstants.MAX_NODE_IOR_COUNT-1)
        msg.instr.src_a_ip = choice((0, 1))
        msg.instr.src_b    = randint(0, nxconstants.MAX_NODE_IOR_COUNT-1)
        msg.instr.src_b_ip = choice((0, 1))
        msg.instr.tgt_reg  = randint(0, nxconstants.MAX_NODE_REGISTERS-1)
        msg.instr.gen_out  = choice((0, 1))
        inbound.append(msg.pack())
        loaded.append(msg.instr.pack())

    # Wait for all inbound drivers to drain
    dut.info(f"Waiting for {len(loaded)} loads")
    for ib in dut.inbound:
        while ib._sendQ: await RisingEdge(dut.clk)
        while ib.intf.valid == 1: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the instruction counters
    assert dut.dut.dut.store.instr_count_o == len(loaded), \
        f"Expected {len(loaded)}, got {int(dut.dut.dut.store.instr_count_o)}"

    # Check the loaded instructions
    for op_idx, op in enumerate(loaded):
        got = int(dut.dut.dut.store.ram.memory[op_idx])
        assert got == op, f"O{op_idx} - exp {hex(op)}, got {hex(got)}"
