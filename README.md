<p align="center">
    <img src="./docs/images/logo_small.png">
</p>

<p align="center">
    RTL simulation acceleration on FPGA
</p>

---

<p align="center">
    <a href="./docs/architecture.md">Architecture</a> | <a href="./docs/tech_stack.md">Technology Stack</a> | <a href="./docs/getting_started.md">Getting Started</a> | <a href="#fpga-synthesis-results">Synthesis Results</a>
</p>

---

## What is Nexus?
Nexus aims to accelerate RTL simulations on commodity FPGA hardware using only free or opensource tools. At present, the system is only a proof-of-concept as the maximum capacity of a 256 node mesh would be 2048 flops, with this configuration easily filling a Xilinx XC7A200T (largest Xilinx FPGA not requiring a paid license). There is lots of scope for refining the system to increase its capacity, some of which is detailed in sections below.

Nexus is a mesh processor - each node is a logic processor capable of performing boolean logic functions on an array of input signals to produce an array of output signals. The node executes a very simple instruction set, only consisting of logic manipulations (e.g. AND, OR, INVERT) without jump or branch operations. An internal array of working registers allow temporary values to be stored and reused, while results can be exposed as outputs to other nodes in the mesh.

Flop-to-flop logic operations will ideally complete within a single node, but sometimes the capacity of one node is not enough (too many logic stages or input signals) in which case an operation can span over multiple nodes in the mesh. Signal state is communicated through a mesh-based messaging fabric, allowing every node to communicate with any other node. Both sequential and combinatorial values are passed through the fabric, but how the receiver handles them is different:

 * Combinatorial updates cause instruction execution within the receiving node to restart using the updated input values;
 * Sequential updates are held until the next simulated clock cycle, then used as the inputs to the next computation.

The node producing the output value sets a flag in the emitted message to distinguish sequential signals from combinatorial updates on a target-by-target basis. The target node's input handling is relatively simple, and treats the update however it was specified in the message.

The same messaging fabric used for carrying the signal state updates is also used to configure and load instructions into every node. The messaging fabric is flexible, and new message types could be added in future to support new functionality.

The backbone of the messaging fabric is built right into the node, with every node able to communicate with its nearest neighbours to the north, east, south, and west. This simplifies the design of the system, removing the need for an independent framework for message routing, and allows reuse of hardware within the node.

A global 'trigger' signal synchronises the operation of all nodes in the mesh. The trigger pulses high to start each simulated clock cycle, and won't rise again until all nodes return to a quiescent state. This allows simulated time to be halted on any clock boundary, and will be key in providing external stimulus to the design.

## Limitations
As Nexus is only a proof-of-concept, there are number of major limitations to be aware of:

 1. Capacity is currently very limited - a 256 node mesh can support a maximum of 2048 flops providing every input is sequential.
 2. Only a single clock domain is supported and logic can only be rising edge triggered.
 3. Flops can only be reset to a low logic state.
 4. External inputs are not yet supported - designs must be self-sustaining (outputs are accessible).
 5. Only output signal values can be recorded, no ability to probe into the design.
 6. No form of debug triggering exists (i.e. cannot wait for a certain signal value).
 7. Constants will be propagated through flops regardless of their reset value, this means any logic requiring a state for a single cycle after reset will be broken.
 8. Only gates and flops are currently supported - RAMs, ROMs, and other types of memory are not.
 9. No support for bidirectional I/O.

These limitations will be overcome in time, some of them are only due to the current software maturity (e.g. 3 & 4) as the mesh is already capable of supporting them.

## Planned Improvements
From this proof-of-concept design, there are a number of obvious improvements required:

 * Use temporary registers to hold state between cycles allowing for flops to exist within a node - at the moment a flop can only exist on the inputs to a node, which means extra hardware to handle mapping outputs back to inputs (wastes I/O and is more costly than necessary);
 * Add a control command allowing for the behaviour of nodes to be configured dynamically;
 * Move away from using explicit operations like AND, OR, INVERT and instead use a truth table encoded within the instruction - the compiler will need to assemble these truth tables on the fly;
 * Add support for three input operations - the compiler will need to collapse one and two input operations until it achieves a three input operation then generate the associated truth table;
 * Add support for multiple phases of execution - dividing the entire design on purely sequential boundaries and executing each phase in a loop (this will require an inter-phase message store in RAM).

## FPGA Synthesis Results

Version 0.2 is the first release to achieve a fully functioning design which meets timing and operates correctly when running on a FPGA (a Xilinx Artix-7 200T). The implementation utilisation report for a 6x6 mesh with each node having 8 inputs, 8 outputs, and 8 working registers is as follows:

| Design Unit  | LUTs           | Slice Registers | F7 Muxes    | F8 Muxes   | Block RAMs |
|--------------|----------------|-----------------|-------------|------------|------------|
| nexus        | 19105 (14.3 %) | 30333 (11.3 %)  | 791 (1.2 %) | 58 (0.2 %) | 36 (9.9 %) |
| - nx_control | 151   (0.1 %)  | 194    (0.1 %)  | 0           | 0          | 0          |
| - nx_mesh    | 18952 (14.2 %) | 30059 (11.2 %)  | 791 (1.2 %) | 58 (0.2 %) | 36 (9.9 %) |

**NOTE:** Percentages indicate proportion of total resources on an Artix-7 200T.

The implementation utilisation report for a typical node within the mesh is as follows:

| Design Unit             | LUTs | Slice Registers | F7 Muxes | F8 Muxes | Block RAMs |
|-------------------------|------|-----------------|----------|----------|------------|
| nx_node                 | 571  | 877             | 23       | 2        | 1          |
| - nx_stream_arbiter     | 43   | 37              | 0        | 0        | 0          |
| - nx_stream_combiner    | 20   | 35              | 0        | 0        | 0          |
| - nx_stream_distributer | 123  | 264             | 0        | 0        | 0          |
| - nx_msg_decoder        | 72   | 94              | 0        | 0        | 0          |
| - nx_node_control       | 244  | 387             | 21       | 0        | 0          |
| - nx_node_store         | 16   | 9               | 0        | 0        | 1          |
| - nx_node_core          | 53   | 50              | 2        | 2        | 0          |

With these utilisation figures timing for the mesh was met at 200 MHz, while the wrapper logic (including the PCIe DMA) was clocked at 125 MHz.
