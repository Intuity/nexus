# Nexus

Mesh based RTL simulation accelerator.

## Model
The `model` folder contains an architectural model of Nexus, which uses the [SimPy](http://simpy.readthedocs.io) discrete event simulation framework. This can model an arbitrary mesh configuration and run basic simulations.

## Compiler
The `compiler` folder contains the flow for translating Yosys' JSON output into instructions which can run on a Nexus mesh.

### Parser
The `compiler/parser` folder contains a Python module capable of parsing Yosys' JSON output and converting it into an explorable model of the design.

## Tests
The `tests` folder contains basic RTL designs and synthesis flows for generating Yosys JSON inputs into the compiler.
