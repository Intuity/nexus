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

from cocotb.triggers import ClockCycles, First, RisingEdge

from nxconstants import Instruction, Operation

from ..testbench import testcase

def rand_instr():
    instr          = Instruction()
    instr.opcode   = choice(list(filter(lambda x: x != Operation.RESERVED, Operation)))
    instr.src_a    = randint(0, 31)
    instr.src_a_ip = choice((0, 1))
    instr.src_b    = randint(0, 31)
    instr.src_b_ip = choice((0, 1))
    instr.tgt_reg  = randint(0, 31)
    instr.gen_out  = choice((0, 1))
    return instr

def evaluate(opcode, val_a, val_b):
    if   opcode == Operation.INVERT: return (0 if val_a else 1)
    elif opcode == Operation.AND   : return (val_a & val_b)
    elif opcode == Operation.NAND  : return (0 if (val_a & val_b) else 1)
    elif opcode == Operation.OR    : return (val_a | val_b)
    elif opcode == Operation.NOR   : return (0 if (val_a | val_b) else 1)
    elif opcode == Operation.XOR   : return (val_a ^ val_b)
    elif opcode == Operation.XNOR  : return (0 if (val_a ^ val_b) else 1)
    raise Exception(f"Unsupported opcode {opcode}")

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
        return memory[address].pack()
    dut.instr_store.resp_cb = get_data

    for idx in range(10):
        dut.info(f"Iteration {idx}")

        # Clear memory
        dut.info("Clearing simulated memory")
        while memory: memory.pop()

        # Generate a bunch of random instructions
        gen_outputs = 0
        actv_regs   = 0
        dut.info("Generating randomised instructions")
        for instr_idx in range(randint(50, 100)):
            dut.info(f"Generating instruction {instr_idx}")
            while True:
                dut.info("Call randomise")
                instr = rand_instr()
                dut.info("Randomise returned")
                # If instruction uses a register, ensure it's been initialised
                if not instr.src_a_ip and ((actv_regs >> (instr.src_a % 8)) & 0x1) == 0:
                    dut.info("Input A not initialised")
                    continue
                if not instr.src_b_ip and ((actv_regs >> (instr.src_b % 8)) & 0x1) == 0:
                    dut.info("Input B not initialised")
                    continue
                # This one is good
                break
            # Append to the memory
            dut.info("Appending to memory")
            memory.append(instr)
            # Mark a register as active
            dut.info("Marking active register")
            actv_regs |= 1 << (instr.tgt_reg % 8)
            # Mark an output as consumed
            dut.info("Marking output as consumed")
            if memory[-1].gen_out:
                gen_outputs += 1
                if gen_outputs >= 8: break
        dut.info(f"Generated {len(memory)} random instructions")

        # Generate a random starting point & setup I/O
        inputs = randint(0, (1 << 32) - 1)
        dut.info(f"Setting input vector to {inputs:032b}")
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
            dut.info(f"Setting input vector to {inputs:032b}")
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

        # Log the final input vector
        dut.info(f"Final input vector: {inputs:032b}")

        # Calculate the expected output
        working = [0] * 8
        outputs = []
        for idx, instr in enumerate(memory):
            dut.info(f"{idx:03d}: {instr}")
            val_a = (
                ((inputs >> instr.src_a) & 0x1)
                if instr.src_a_ip else
                working[instr.src_a % 8]
            )
            val_b = (
                ((inputs >> instr.src_b) & 0x1)
                if instr.src_b_ip else
                working[instr.src_b % 8]
            )
            working[instr.tgt_reg % 8] = int(evaluate(instr.opcode, val_a, val_b))
            if instr.gen_out: outputs.append(working[instr.tgt_reg % 8])
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
