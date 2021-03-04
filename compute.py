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

import click
from vcd import VCDWriter

class Operation(IntEnum):
    INVERT = 0
    AND    = 1
    NAND   = 2
    OR     = 3
    NOR    = 4
    XOR    = 5
    XNOR   = 6

    @classmethod
    def evaluate(self, op, *inputs):
        if op == Operation.INVERT:
            assert len(inputs) == 1
            return not inputs[0]
        else:
            assert len(inputs) == 2
            if   op == Operation.AND : return     (inputs[0] and inputs[1])
            elif op == Operation.NAND: return not (inputs[0] and inputs[1])
            elif op == Operation.OR  : return     (inputs[0] or inputs[1])
            elif op == Operation.NOR : return not (inputs[0] or inputs[1])
            elif op == Operation.XOR : return     (inputs[0] ^ inputs[1])
            elif op == Operation.XNOR: return not (inputs[0] ^ inputs[1])
            else: raise Exception(f"Unknown operation {op}")

class Phases(IntEnum):
    WAIT = 0
    RUN  = 1

class Trigger:

    def __init__(self, tx_node, tx_index, rx_node, rx_index):
        self.tx_node  = tx_node
        self.tx_index = tx_index
        self.rx_node  = rx_node
        self.rx_index = rx_index

    def __repr__(self):
        return (
            f"<TXN[{self.tx_node}].Is[{self.tx_index}] -> "
            f"RXN[{self.rx_node}].In[{self.rx_index}]>"
        )
    def __str__(self): return self.__repr__()

class Instruction:

    def __init__(self, op, inputs, target, triggers):
        self.op       = op
        self.inputs   = inputs
        self.target   = target
        self.triggers = triggers

    def __repr__(self):
        return (
            f"{self.op.name}(" +
            ", ".join([f"R[{x}]" for x in self.inputs]) +
            f") -> R[{self.target}]" +
            (f" -> {len(self.triggers)} message(s)" if self.triggers else "")
        )

    def __str__(self): return self.__repr__()

class Node:

    def __init__(self, inputs=4, outputs=4, registers=16):
        self.inputs       = [False] * inputs
        self.registers    = [False] * registers
        self.instructions = []
        self.outputs      = [None] * outputs
        self.cycle        = 0
        self.step         = 0
        self.phase        = Phases.WAIT

    @property
    def waiting(self): return self.phase == Phases.WAIT
    @property
    def running(self): return self.phase == Phases.RUN

    def load(self, instr_seq, conn_map):
        self.instructions = []
        for idx, instr in enumerate(instr_seq):
            # Build messages to propagate
            triggers = [
                Trigger(0, instr["output"], 0, x) for x in conn_map.get(str(instr["output"]), [])
            ] if "output" in instr else []
            # Build the instruction
            self.instructions.append(Instruction(
                Operation[instr["op"]], instr["inputs"], instr["target"],
                triggers
            ))
            print(f"Load {idx:03d}: {self.instructions[-1]}")

    def tick(self, sync=False):
        assert (self.phase == Phases.WAIT) or not sync
        if self.phase == Phases.WAIT and sync:
            for idx, val in enumerate(self.inputs): self.registers[idx] = val
            self.phase = Phases.RUN
            print(
                f"Starting cycle {self.cycle} - entering run phase: " +
                " ".join([("1" if x else "0") for x in self.inputs])
            )
        elif self.phase == Phases.RUN:
            instr  = self.instructions[self.step]
            result = Operation.evaluate(
                instr.op, *[self.registers[x] for x in instr.inputs]
            )
            # print(
            #     f"Cycle {self.cycle:03d}, step {self.step:03d} -> "
            #     f"{instr.op.name}(" +
            #     ", ".join([("1" if self.registers[x] else "0") for x in instr.inputs]) +
            #     f") = {'1' if result else '0'}"
            # )
            self.registers[instr.target] = result
            for trigger in instr.triggers:
                self.inputs[trigger.rx_index] = result
            self.step += 1
            if self.step >= len(self.instructions):
                self.phase  = Phases.WAIT
                self.step   = 0
                self.cycle += 1

n = Node()
with open("instr_seq.json") as fh:
    data = json.load(fh)
    n.load(data["instructions"], data["connections"])

with open("sim.vcd", "w") as fh:
    with VCDWriter(fh, timescale="1 ns", date="today") as vcd:
        cycle     = vcd.register_var("tb",      "cycle",     "integer", size=32)
        inputs    = vcd.register_var("tb.node", "inputs",    "integer", size=4)
        registers = vcd.register_var("tb.node", "registers", "integer", size=16)
        for step in range(1000):
            if n.waiting:
                vcd.change(cycle,     step, n.cycle)
                vcd.change(inputs,    step, sum([((1 if x else 0) << i) for i, x in enumerate(n.inputs)]))
                vcd.change(registers, step, sum([((1 if x else 0) << i) for i, x in enumerate(n.registers)]))
            n.tick(sync=n.waiting)
