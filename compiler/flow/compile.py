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

from enum import IntEnum
import json
import logging

from ..models.gate import Gate, Operation
from .plot import plot_group

log = logging.getLogger("compiler.compile")

class Instruction:

    def __init__(self, op, inputs, output):
        self.op     = op
        self.inputs = inputs[:]
        self.output = output

    def __repr__(self):
        return (
            f"{self.op.name}(" +
            ", ".join([f"R{x.index}" for x in self.inputs]) +
            (f") -> {self.output}" if self.output != None else ")")
        )

class Register:

    def __init__(self, index, value=None, protect=False):
        self.index   = index
        self.value   = value
        self.age     = 0
        self.protect = protect

    def __repr__(self):
        return (
            f"<Register[{self.index}] - V: {self.value if self.value else 'N/A'}"
            f", A: {self.age}, P: {self.protect}>"
        )

    @property
    def vacant(self): return (self.value == None)

    def step(self):
        if self.value != None: self.age += 1

    def set(self, value):
        """ Set a new value for the register """
        self.value = value
        self.age   = 0

    def clear(self):
        """ Clears the register entirely (value, protection, and age) """
        self.value   = None
        self.protect = False
        self.age     = 0

    def refresh(self):
        """ Clears the age back to zero while preserving other attributes """
        self.age = 0

def compile(module, groups):
    # Sort groups from least to most complex
    groups = sorted(groups[9:13], key=lambda x: len(x[2]), reverse=False)
    # for idx, (flop, inputs, logic) in enumerate(groups):
    #     plot_group(flop, inputs, logic, f"group_{idx}.png")
    # For the selected groups, get unique input
    primary = set([y[0] for x in groups for y in x[1]])
    log.info(f"Identified {len(primary)} primary inputs")
    # Setup initial state
    log.info("Setting up initial register state")
    registers = (
        [Register(i, x, protect=True) for i, x in enumerate(primary)] +
        [Register(i) for i in range(len(primary), 16)]
    )
    # Count how many times each term is used all final expressions
    term_counter = {}
    def chase(bit):
        if not str(bit) in term_counter: term_counter[str(bit)] = 0
        term_counter[str(bit)] += 1
        if isinstance(bit, Gate):
            for in_bit in bit.inputs: chase(in_bit)
    for flop, _, _ in groups: chase(flop.input[0].driver)
    # Start assembling logic
    log.info(f"Assembling {len(groups)} groups")
    outputs      = []
    instructions = []
    for idx, (flop, inputs, logic) in enumerate(groups):
        log.info(f" - Group {idx} - converting {len(logic)} gates")
        # Construct missing components
        for term, _ in logic:
            # If this term is already computed, skip it
            if str(term) in (str(x.value) for x in registers):
                log.info(f"  + Skipping term {term} as already computed")
                continue
            # Identify a target register
            target = None
            for reg in registers:
                # Always skip protected registers
                if reg.protect: continue
                # Check if register value is still a required term
                if term_counter.get(str(reg.value), 0) > 0: continue
                # Is this vacant, or older than the current target?
                if reg.vacant or (not target) or (target.age < reg.age):
                    target = reg
            # If no vacant registers, abort
            if not target:
                raise Exception(f"No target register available for term {term}")
            # Log what we're doing
            log.info(f"  + Placing term {term} into register {target.index}")
            # Identify input term sources
            reg_in = []
            for subterm in term.inputs:
                found = [x for x in registers if str(x.value) == str(subterm)]
                if not found:
                    raise Exception(f"Could not find source for sub-term {subterm}")
                log.info(f"  + Using register {found[0].index} for sub-term {subterm}")
                reg_in.append(found[0])
                # Track as terms are consumed
                term_counter[str(subterm)] -= 1
                # Refresh age counter
                found[0].refresh()
            # If this is the end of the logic chain, construct an output
            output = len(outputs) if (term == logic[-1][0]) else None
            # Record the instruction
            instructions.append(Instruction(term.op, reg_in, output))
            # Update register state for the next operation
            target.set(term)
            # If this is the final stage, record the output
            if output != None:
                outputs.append((len(instructions)-1, flop, output))
                term_counter[str(flop.input[0].driver)] -= 1
            # Increment age of all register values
            for reg in registers: reg.step()
    # Form connections between outputs and inputs
    print("Connections:")
    enc_conn = []
    for idx, input in enumerate(primary):
        sources = [
            x for x in outputs if
            (x[1].output     and x[1].output[0]     == input) or
            (x[1].output_inv and x[1].output_inv[0] == input)
        ]
        if len(sources) != 1:
            raise Exception(f"Failed to identify unique source for {input}")
        print(f"O[{sources[0][0]}] -> I[{idx}]")
        enc_conn.append((sources[0][0], idx))
    enc_conn.sort(key=lambda x: x[0])
    print("")
    # Print instructions
    print("Instructions:")
    enc_inst = []
    for idx, instr in enumerate(instructions):
        print(f" - {idx:03d}: {instr}")
        data = {
            "comment": str(instr),
            "op"     : instr.op.name,
            "inputs" : [x.index for x in instr.inputs],
        }
        if instr.output != None: data["output"] = instr.output
        enc_inst.append(data)
    print("")
    with open("instr_seq.json", "w") as fh:
        json.dump({
            "instructions": enc_inst,
            "connections" : enc_conn,
        }, fh, indent=4)
    import pdb; pdb.set_trace()
