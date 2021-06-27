<p align="center">
    <img src="./docs/images/logo_small.png">
</p>

<p align="center">
    Open source RTL simulation acceleration on commodity hardware
</p>

---

## What is Nexus?
Nexus aims to accelerate RTL simulations on commodity FPGA hardware using only free or opensource tools. At present, the system is only a proof-of-concept as the maximum capacity of a 256 node mesh would be 2048 flops, with this configuration easily filling a Xilinx XC7A200T (largest Xilinx FPGA not requiring a paid license). There is lots of scope for refining the system to increase its capacity, some of which are detailed in sections below.

At the heart of Nexus is a mesh processor. Each node in the mesh is a logic processor able to perform boolean logic functions on an array of input signals to produce an array of output signals. The node executes a very simple instruction set, only consisting of logic manipulations (e.g. AND, OR, INVERT) without jump or branch operations. An internal array of working registers allow temporary values to be stored and reused, while results can be exposed as outputs to other nodes in the mesh.

Flop-to-flop logic operations will ideally complete within a single node, but sometimes the capacity of one node is not enough (too many logic stages or input signals) in which case an operation can span over multiple nodes in the mesh. Signal state is communicated through a mesh-based messaging fabric, allowing every node in the mesh to communicate with any other node either directly or through broadcast. Both sequential and combinatorial values are passed by through the fabric, but how the receiver handles them is different:

 * Combinatorial updates cause instruction execution within the receiving node to restart, using the new value;
 * Sequential updates are held by the receiving node's control block until the next simulated clock cycle, then used as the inputs to the next run through the instruction list.

Whether signal state is combinatorial or sequential is decided by the input configuration of the receiving node, the node emitting the state message is not aware of how it will be consumed.

The same messaging fabric used for carrying the signal state updates is also used to load instructions into each node as well as configuring the input and output signal mappings. The messaging fabric is flexible, and new message types could be added in future to support new functionality.

The backbone of the messaging fabric is built right into the node, with each node able to communicate with its neighbour to the north, east, south, and west. This simplifies the design of the system, removing the need for an independent framework for message parsing, and allows reuse of each node's message decoder for routing messages.

A global 'trigger' signal synchronises the operation of all nodes in the mesh. The trigger pulses high to start each simulated clock cycle, and won't rise again until all nodes return to their idle state. This allows simulated time to be halted on any clock boundary, and will be key in providing external stimulus to the design.

## Limitations
As Nexus is only a proof-of-concept, there are number of major limitations to be aware of:

 1. Capacity is currently very limited - a 256 node mesh can support a maximum of 2048 flops providing every input is sequential.
 2. Only a single clock domain is supported and logic can only be rising edge triggered.
 3. Flops can only be reset to a low logic state.
 4. External inputs are not yet supported - designs must be self-sustaining (outputs are accessible).

These limitations will be overcome in time, some of them are only due to the current software maturity (e.g. 3 & 4) as the mesh is already capable of supporting them.

## Model
The `nxmodel` folder contains an architectural model of Nexus, which uses the [SimPy](http://simpy.readthedocs.io) discrete event simulation framework. This can model an arbitrary mesh configuration and run basic simulations.

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
