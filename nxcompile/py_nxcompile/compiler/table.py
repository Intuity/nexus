from tabulate import tabulate

class Table:

    ID = 0

    def __init__(self, op, inputs, outputs, ops):
        self.id       = Table.ID
        Table.ID     += 1
        self.op       = op
        self.inputs   = inputs
        self.outputs  = outputs
        self.ops      = ops

    @property
    def name(self):
        return f"TT{self.id}"

    @property
    def all_inputs(self):
        return self.inputs + sum((x.all_inputs for x in self.inputs if isinstance(x, Table)), [])

    def explode(self):
        for input in self.inputs:
            if isinstance(input, Table):
                yield from input.explode()
        yield self

    def display(self):
        print(tabulate(
            [
                ([y for y in f"{x:0{len(self.inputs)}b}"] + [self.outputs[x]])
                for x in range(2 ** len(self.inputs))
            ],
            headers=[x.name for x in self.inputs] + ["R"],
        ))
