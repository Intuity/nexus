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
 5. Only output signal values can be recorded, no ability to probe into the design.
 6. No form of debug triggering exists (i.e. cannot wait for a certain signal value).
 7. Mesh network can easily deadlock, current workaround is a large (expensive) FIFO inside each node but a better solution needs to be found.
 8. Constants will be propagated through flops regardless of their reset value, this means any logic requiring a state for a single cycle after reset will be broken.
 9. Only gates and flops are currently supported - RAMs, ROMs, and other types of memory are not.
 10. No support for bidirectional I/O.

These limitations will be overcome in time, some of them are only due to the current software maturity (e.g. 3 & 4) as the mesh is already capable of supporting them.

## Technology Stack
The mesh itself is a relatively simple machine, and is intrinsically linked to a custom compiler to make it behave in a sensible fashion. The compiler in turn relies on [yosys](https://github.com/YosysHQ/yosys) to perform the transformation from RTL into a generic cell mapped design.

### nxcompile
Starting with the JSON export of the synthesised RTL from [yosys](https://github.com/YosysHQ/yosys), the compiler is responsible for producing a design which can run on the mesh. This not only includes producing the instruction listing for each node, but also the input and output mappings, and the messages which pass between the nodes.

The compiler works through a number of steps to transform the design:

 1. Flattens all hierarchy from the Yosys export creating a single module containing all logical operations;
 2. Performs constant propagation to simplify the design - stripping out any gates or flops that produce a static value (see limitation 8 above);
 3. Duplicated gates are eliminated;
 4. Chains of inverters are truncated;
 5. Gates and flops are then converted into instructions and input/output mappings (without yet assigning them to a node);
 6. Placement of each instruction then starts following the procedure:
    1. First operation is placed into any node;
    2. If the next operation is not dependent on any previous operation, it is placed into the next node with spare capacity;
    3. If the next operation is dependent on a previous operation then the compiler will:
        * attempt to place it into the same node as the operation it depends upon,
        * if that's not possible then the compiler will attempt to transfer the entire logic tree (including the new operation) into a different node,
        * finally if the operation still isn't placed then the compiler will place it in the nearest node with spare capacity.
 7. Once all operations are placed, the compiler then runs a further compilation step on each node which assigns input and output positions as well as use of the temporary registers.
 8. Finally, input and output positions are linked to configure the messages each node will produce.

The compiler can undoubtedly be optimised to improve instruction placement as well as input and output mappings, this will help to increase the capacity of the platform.

The compiler can be run by executing `./bin/nxcompile` or `python3 -m nxcompile` - an example of its use is shown in a section below.

### nxmodel
To aid development of the compiler and provide a golden reference for the RTL design, an architectural model of Nexus was developed using the [SimPy](http://simpy.readthedocs.io) discrete event simulation framework. This tool can model any configuration of the mesh, and provides VCD capture as well as debug logging as the design runs.

Just like the RTL design, the model is composed of nodes within a mesh:

 * The `Node` class, defined in `nxmodel/node.py`, represents a single node and can decode and execute instructions produced by the compiler. It is also responsible for consuming, routing, decoding, and emitting messages (which are defined in `nxmodel/message.py`).
 * The `Mesh` class, defined in `nxmodel/mesh.py`, sets up the required number of `Node` instances and links them together.

The model can be run by executing `./bin/nxmodel` or `python3 -m nxmodel`.

### nxdisasm
Debugging a design spread across a mesh network is tricky, especially when the compiler and model are untrusted. To go some way to solving this problem, the disassembler consumes a design produced by `nxcompile` and produces two outputs:

 * A listing of the instruction set for every node in the design (helpful for hand-calculating the output state);
 * A Verilog version of the translated design, which can be simulated under the same testbench to check for consistent behaviour in a trusted simulator.

The disassembler can be run by executing `./bin/nxdisasm` or `python3 -m nxdisasm`.
