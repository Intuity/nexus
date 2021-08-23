<p align="center">
    <img src="./images/logo_small.png">
</p>

---

# Technology Stack
The mesh itself is a relatively simple machine, and is intrinsically linked to a custom compiler to make it behave in a sensible fashion. The compiler in turn relies on [yosys](https://github.com/YosysHQ/yosys) to perform the transformation from RTL into a generic cell mapped design.

## nxcompile
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

## nxmodel
To aid development of the compiler and provide a golden reference for the RTL design, an architectural model of Nexus was developed using the [SimPy](http://simpy.readthedocs.io) discrete event simulation framework. This tool can model any configuration of the mesh, and provides VCD capture as well as debug logging as the design runs.

Just like the RTL design, the model is composed of nodes within a mesh:

 * The `Node` class, defined in `nxmodel/node.py`, represents a single node and can decode and execute instructions produced by the compiler. It is also responsible for consuming, routing, decoding, and emitting messages (which are defined in `nxmodel/message.py`).
 * The `Mesh` class, defined in `nxmodel/mesh.py`, sets up the required number of `Node` instances and links them together.

The model can be run by executing `./bin/nxmodel` or `python3 -m nxmodel`.

## nxdisasm
Debugging a design spread across a mesh network is tricky, especially when the compiler and model are untrusted. To go some way to solving this problem, the disassembler consumes a design produced by `nxcompile` and produces two outputs:

 * A listing of the instruction set for every node in the design (helpful for hand-calculating the output state);
 * A Verilog version of the translated design, which can be simulated under the same testbench to check for consistent behaviour in a trusted simulator.

The disassembler can be run by executing `./bin/nxdisasm` or `python3 -m nxdisasm`.