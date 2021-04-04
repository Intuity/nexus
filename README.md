# Nexus

Mesh based RTL simulation accelerator.

## Model
The `nxsimulate` folder contains an architectural model of Nexus, which uses the [SimPy](http://simpy.readthedocs.io) discrete event simulation framework. This can model an arbitrary mesh configuration and run basic simulations.

## Compiler
The `nxcompile` folder contains the flow for translating Yosys' JSON output into instructions which can run on a Nexus mesh.

### Parser
The `nxcompile/parser` folder contains a Python module capable of parsing Yosys' JSON output and converting it into an explorable model of the design.

### Current Limitations
There are a number of limitations with the compiler at the moment - not because these items are impossible to address, but instead to reduce complexity in the initial implementation:

 * Only a single clock domain is supported, with no support for clock gating
 * Flops do not support an enable signal - so will always propagate a value
 * Flops do not have a reset value input - so will always reset to Q=0
 * Constants attached to a flop's D input will always be propagated through the flop - regardless of what the reset state of the flop should be (this means if a high value is driven on a flop input, the flop will be flattened and the Q output will be driven statically high - even if the intention was to create an initial state)
 * No support for memories - only gates and flops are currently supported
 * No support for bidirectional I/O

## Tests
The `tests` folder contains basic RTL designs and synthesis flows for generating Yosys JSON inputs into the compiler.

## RTL/Hardware
The `hardware` folder contains the Verilog implementation of Nexus accelerator, including testbenches.
