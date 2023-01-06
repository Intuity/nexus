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

from functools import reduce

from nxcompile import NXFlop, NXPort, nxgate_op_t

class Operation:

    def __init__(self, gate, *inputs):
        self.gate   = gate
        self.inputs = list(inputs)

    @property
    def op(self):
        return self.gate.op

    def sub_ops(self):
        for input in self.inputs:
            if isinstance(input, Operation):
                yield input
                yield from input.sub_ops()

    def render(self, include=None):
        if include and self not in include:
            return f"<{self.gate.name}>"
        def name(obj):
            if isinstance(obj, NXPort):
                return "P:" + obj.name
            elif isinstance(obj, NXFlop):
                return "F:" + obj.name
            else:
                return obj.render(include=include)
        if self.op == nxgate_op_t.COND:
            return (
                "(" + name(self.inputs[0]) + ") ? " +
                "(" + name(self.inputs[1]) + ") : " +
                "(" + name(self.inputs[2]) + ")"
            )
        elif self.op == nxgate_op_t.NOT:
            return "!(" + name(self.inputs[0]) + ")"
        else:
            op_str = {
                nxgate_op_t.AND : " & ",
                nxgate_op_t.OR  : " | ",
                nxgate_op_t.XOR : " ^ ",
            }[self.op]
            return op_str.join([("(" + name(x) + ")") for x in self.inputs])

    def prettyprint(self):
        op_str   = self.render()
        pretty   = ""
        brackets = 0
        indents  = []
        for idx, char in enumerate(op_str):
            next = op_str[idx+1] if (idx + 1) < len(op_str) else None
            if char == "(":
                brackets += 1
                if next == "(":
                    indents.append(brackets)
                    pretty += "(\n" + ((len(indents) * 4) * " ")
                else:
                    pretty += "("
            elif char == ")":
                if brackets in indents:
                    indents.pop()
                    pretty += "\n" + ((len(indents) * 4) * " ") + ")"
                else:
                    pretty += ")"
                brackets -= 1
            else:
                pretty += char
        return pretty

    def __repr__(self) -> str:
        return self.render()

    def __str__(self):
        return self.__repr__()

    def evaluate(self, values):
        # Gather the finalised input values from sub-operations
        final = []
        for term in self.inputs:
            if term in values:
                final.append(values[term])
            elif isinstance(term, Operation):
                final.append(term.evaluate(values))
            else:
                raise Exception("Missing term")
        # Evaluate
        if self.gate.op == nxgate_op_t.COND:
            return final[1:][final[0]]
        elif self.gate.op == nxgate_op_t.AND:
            return reduce(lambda x, y: x & y, final)
        elif self.gate.op == nxgate_op_t.OR:
            return reduce(lambda x, y: x | y, final)
        elif self.gate.op == nxgate_op_t.XOR:
            return reduce(lambda x, y: x ^ y, final)
        elif self.gate.op == nxgate_op_t.NOT:
            return [1, 0][final[0]]
        else:
            raise Exception("Unsupported operation")
