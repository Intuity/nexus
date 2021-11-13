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

from cocotb.triggers import RisingEdge

from node.instrs import gen_instructions, eval_instruction
from nxconstants import MAX_NODE_MEMORY

from ..testbench import testcase

@testcase()
async def execute(dut):
    """ Test execution of different operations """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Read back parameters from the design
    num_inputs    = int(dut.dut.INPUTS)
    num_outputs   = int(dut.dut.OUTPUTS)
    num_registers = int(dut.dut.REGISTERS)

    # Decide on a number of instructions to execute
    num_instr = randint(10, MAX_NODE_MEMORY)

    # Generate an instruction stream and write it to memory
    instrs = gen_instructions(num_instr, num_inputs, num_outputs, num_registers)
    for idx, instr in enumerate(instrs):
        dut.ram.memory[idx] = instr.pack()
    dut.populated <= len(instrs)

    # Track input, output, and register state
    inputs  = [0] * num_inputs
    outputs = [0] * num_outputs
    working = [0] * num_registers

    # Run multiple iterations
    for _ in range(100):
        # Randomise the input state
        inputs = [choice((0, 1)) for _ in range(num_inputs)]
        dut.inputs <= sum(((x << i) for i, x in enumerate(inputs)))
        # Trigger the design
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        # Wait for IDLE to go low, then return to high
        while dut.idle == 1: await RisingEdge(dut.clk)
        while dut.idle == 0: await RisingEdge(dut.clk)
        # Evaluate the instruction stream
        out_idx = 0
        for instr in instrs:
            working, gen_out, result = eval_instruction(instr, inputs, working)
            if gen_out:
                outputs[out_idx] = result
                out_idx += 1
        # Check the modelled output state against the RTL
        for index, mdl in enumerate(outputs):
            rtl = int(dut.outputs[index])
            assert mdl == rtl, f"O[{index}] - Model: {mdl}, RTL: {rtl}"
        # Check the modelled register state against the RTL
        for index, mdl in enumerate(working):
            rtl = int(dut.dut.u_dut.working_q[index])
            assert mdl == rtl, f"R[{index}] - Model: {mdl}, RTL: {rtl}"
