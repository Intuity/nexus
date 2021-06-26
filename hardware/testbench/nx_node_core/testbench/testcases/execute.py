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

from cocotb.triggers import ClockCycles, First, RisingEdge

from nxmodel.node import Instruction, Operation

from ..testbench import testcase

@testcase()
async def execute(dut):
    """ Test execution of different operations """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Register a callback with the instruction store responder
    memory = []
    def get_data(_driver, address):
        assert address >= 0 and address < len(memory), \
            f"Address {address} is outside valid range 0-{len(memory)-1}"
        return memory[address].raw
    dut.instr_store.resp_cb = get_data

    for _ in range(10):
        # Clear memory
        while memory: memory.pop()

        # Generate a bunch of random instructions
        gen_outputs = 0
        actv_regs   = 0
        for _ in range(randint(50, 100)):
            while True:
                instr = Instruction.randomise()
                # If instruction uses a register, ensure it's been initialised
                if not instr.is_input_a and ((actv_regs >> instr.source_a) & 0x1) == 0:
                    continue
                if not instr.is_input_b and ((actv_regs >> instr.source_b) & 0x1) == 0:
                    continue
                # This one is good
                break
            # Append to the memory
            memory.append(instr)
            # Mark a register as active
            actv_regs |= 1 << instr.target
            # Mark an output as consumed
            if memory[-1].is_output:
                gen_outputs += 1
                if gen_outputs >= 8: break
        dut.info(f"Generated {len(memory)} random instructions")

        # Generate a random starting point & setup I/O
        inputs = randint(0, (1 << 8) - 1)
        dut.info(f"Setting input vector to {inputs:08b}")
        dut.inputs_i    <= inputs
        dut.populated_i <= len(memory)

        # Trigger DUT
        dut.info("Triggering DUT")
        dut.trigger_i <= 1
        await RisingEdge(dut.clk)
        dut.trigger_i <= 0
        await RisingEdge(dut.clk)
        assert dut.idle_o == 0, "DUT is still idle"

        # Reset a random number of times with altered inputs
        for _ in range(randint(0, 2)):
            await ClockCycles(dut.clk, randint(1, len(memory)))
            inputs = randint(0, (1 << 8) - 1)
            dut.inputs_i  <= inputs
            dut.trigger_i <= 1
            await RisingEdge(dut.clk)
            dut.trigger_i <= 0
            await RisingEdge(dut.clk)
            assert dut.idle_o == 0, "DUT is idle"

        # Wait for DUT to go idle
        await First(ClockCycles(dut.clk, 1000), RisingEdge(dut.idle_o))
        await RisingEdge(dut.clk)
        assert dut.idle_o == 1, "DUT is not idle"

        # Calculate the expected output
        working = [0] * 8
        outputs = []
        for idx, instr in enumerate(memory):
            dut.info(f"{idx:03d}: {instr}")
            val_a = (
                ((inputs >> instr.source_a) & 0x1)
                if instr.is_input_a else
                working[instr.source_a]
            )
            val_b = (
                ((inputs >> instr.source_b) & 0x1)
                if instr.is_input_b else
                working[instr.source_b]
            )
            working[instr.target] = int(Operation.evaluate(instr.op, val_a, val_b))
            if instr.is_output: outputs.append(working[instr.target])
        dut.info(f"Executed {len(memory)} instructions -> {len(outputs)} outputs")

        # Compare and contrast result
        dut.info("Checking outputs against model")
        mismatches = 0
        for idx, output in enumerate(outputs):
            if int(dut.outputs_o[idx]) != output:
                dut.error(
                    f"Output {idx} - exp: {output}, got: {int(dut.outputs_o[idx])}"
                )
                mismatches += 1
        assert mismatches == 0, f"Detected {mismatches} output errors"
