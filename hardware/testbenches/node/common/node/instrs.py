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
from typing import List, Tuple

from nxconstants import (Instruction, MAX_NODE_INPUTS, MAX_NODE_OUTPUTS,
                         MAX_NODE_REGISTERS, MAX_NODE_MEMORY, TT_WIDTH)

def gen_instructions(
    max_ops    : int  = MAX_NODE_MEMORY,
    inputs     : int  = MAX_NODE_INPUTS,
    outputs    : int  = MAX_NODE_OUTPUTS,
    registers  : int  = MAX_NODE_REGISTERS,
    stop_early : bool = True,
) -> List[Instruction]:
    """
    Generate a random instruction stream for the node up to a maximum number,
    also limited by the number of possible outputs.

    Args:
        max_ops   : Maximum number of operations to generate
        inputs    : Number of available inputs
        outputs   : Number of available outputs
        registers : Number of working registers
        stop_early: Stop once all of the outputs have been exhausted
    """
    stream    = []
    reg_used  = [False] * registers
    used_outs = 0
    # Closure function to allocate safe inputs
    def random_source():
        use_reg = (True in reg_used) and choice((True, False))
        if use_reg:
            return False, choice([i for i, x in enumerate(reg_used) if x])
        else:
            return True, randint(0, inputs-1)
    # Generate up to the maximum number of operations
    for _ in range(max_ops):
        a_ip, a_idx = random_source()
        b_ip, b_idx = random_source()
        c_ip, c_idx = random_source()
        stream.append(Instruction(
            truth   =randint(0, (1 << TT_WIDTH) - 1),
            src_a_ip=a_ip, src_a=a_idx,
            src_b_ip=b_ip, src_b=b_idx,
            src_c_ip=c_ip, src_c=c_idx,
            tgt_reg =randint(0, registers - 1),
            gen_out =(choice((0, 1)) if (used_outs < outputs) else 0)
        ))
        # Mark which registers are used
        reg_used[stream[-1].tgt_reg] = True
        # If all outputs exhausted, suppress output generation
        if used_outs >= outputs: stream[-1].gen_out = 0
        # Count outputs being generated
        if stream[-1].gen_out: used_outs += 1
        # Break out early if required
        if used_outs >= outputs and stop_early: break
    return stream

def print_instructions(stream : List[Instruction]) -> None:
    """
    Print out a listing of all of the instructions in a stream.

    Args:
        stream: The instruction stream
    """
    output_idx = 0
    for idx, instr in enumerate(stream):
        print(
            f"{idx:04d} - T: {instr.truth:08b} "
            f"A: {'I' if instr.src_a_ip else 'R'}[{instr.src_a:2d}] "
            f"B: {'I' if instr.src_b_ip else 'R'}[{instr.src_b:2d}] "
            f"C: {'I' if instr.src_c_ip else 'R'}[{instr.src_c:2d}] "
            f"T: R[{instr.tgt_reg:2d}]"
            + (f" -> O[{output_idx:2d}]" if instr.gen_out else "")
        )
        if instr.gen_out: output_idx += 1

def eval_instruction(
    instruction : Instruction,
    inputs      : List[int],
    registers   : List[int],
) -> Tuple[List[int], bool, int]:
    """
    Evaluate an instruction, generating working register and output state after
    the step has completed.

    Args:
        instruction: The instruction to execute
        inputs     : Array of the current inputs
        registers  : Array of the working registers

    Return: Tuple of updated register state, whether an output was generated,
            and the value
    """
    # Pickup the input values
    val_a = inputs[instruction.src_a] if instruction.src_a_ip else registers[instruction.src_a]
    val_b = inputs[instruction.src_b] if instruction.src_b_ip else registers[instruction.src_b]
    val_c = inputs[instruction.src_c] if instruction.src_c_ip else registers[instruction.src_c]
    # Pickout the value from the truth table
    result = (instruction.truth >> ((val_a << 2) | (val_b << 1) | (val_c << 0))) & 0x1
    # Update target register
    working = registers[:]
    working[instruction.tgt_reg] = result
    # Return values
    return (working, instruction.gen_out, result)
