<p align="center">
    <img src="./docs/images/logo_small.png">
</p>

<p align="center">
    FPGA Accelerated RTL Simulation
</p>

---

<p align="center">
    <a href="./docs/architecture.md">Architecture</a> | <a href="./docs/tech_stack.md">Technology Stack</a> | <a href="./docs/getting_started.md">Getting Started</a> | <a href="#fpga-synthesis-results">Synthesis Results</a>
</p>

---

## What is Nexus?

Nexus is a cycle based simulator which runs on FPGA, targeting simulation speeds
above 1 MHz. The hardware supports synchronous inputs and outputs, access to fast
on-device memory, and tracing of all sequential state in the simulated design.

The architecture of Nexus is a [systolic array](https://en.wikipedia.org/wiki/Systolic_array),
a mesh processor formed of many small nodes, each of which simulates a small part
of the overall design. Each node is fully programmable, and executes a stream of
three input operations of any arbitrary boolean function. The inputs to each
operation can be selected from external stimulus, other nodes in the mesh, or a
temporary register, while the output of each operation is stored to a temporary
register and can be shared sequentially or combinationally with other nodes in
the mesh.

Every node in the mesh is connected to its immediate neighbours, and messages
sent through the mesh can be routed to any other node in the system -  allowing
signal state to be sent from any node to any other. This same fabric is reused to
load and configure the mesh, as well as to expose output signals towards the host,
and supports tracing of internal state during simulation.

## Features

The RTL design for Nexus supports a large number of features, and is also highly
configurable. The list below details the main features the hardware supports:

 * Up to 240 nodes are supported in mesh configuration of 15 rows by 16 columns
 * Aggregators terminate each column, collecting signal messages to form the full
   output vector (maximum 512 bits for a 16 column mesh)
 * Nodes in the mesh:
   * Support up to 32 inputs, 32 outputs, and 16 working registers
   * Have 4 kB of RAM shared between the logical and communication programs (one
     block RAM instance)
   * Support dynamic tracing of output values to the host
   * Can loop-back any output to the inputs to support sequential state
 * The mesh controller:
   * Interfaces with the host platform
   * Offers multiple trigger modes allowing the simulation to run continuously,
     in single steps, or for a fixed duration
   * Streams output state at the end of each simulated cycle back to the host
     for analysis and waveform tracing
   * Supports up to 11 on-device simulated memories which can be dynamically
     enabled, allowing RAMs and ROMs to be simulated without host involvement
   * Simulated memories can be accessed by the host at any time, allowing programs
     to be loaded and data dumped out

**NOTE** Not all features offered by the hardware are currently supported by the
compiler - these deficiencies will be addressed in the near future.

## Limitations
### Hardware Limitations

The hardware does have some limitations, some of which can be addressed in future
revisions of the design:

 * No hardware debug triggering exists - if simulation needs to pause when the
   design reaches a certain state, then software will need to single step the
   simulation which is inefficient and slow.
 * While columns can be selectively triggered, there is no hardware support for
   sequencing different columns to simulate multiple clock domains - meaning
   software would have to use single stepping.
 * No support for propagation delays as Nexus is a cycle-based simulator.
 * No support for bi-directional ports.

### Software Limitations

Other restrictions are imposed by the immaturity of the compiler and driver, but
these will be addressed in the near future:

 * External inputs are not yet supported - designs must be self-sustaining.
 * Constants are propagated through flops regardless of their reset value, this
   will break any logic requiring state for only a single cycle after reset.
 * Access to on-device memories is not available.
 * Compiler currently operates on a first fit basis, which can result in poor
   utilisation of node resources.
 * Compiler is not optimised, current implementation in Python only exists as a
   proof of concept - it is slow and computationally intensive, and can only
   handle trivial designs.
 * Compiler does not support three-input operations - it currently emits fixed
   truth tables for one and two input operations such as AND, OR, and NOT.

## Planned Improvements

### Hardware

 * Add a mechanism for triggering which will allow Nexus to automatically pause
   the simulation when the design reaches a certain state.
 * Allow a node's registers to hold state between cycles, providing efficient
   storage for sequential logic that does not need to exit the node.

### Software

 * New, efficient compiler implementation able to utilise all of the resources
   of the hardware (including three input operations, simulated memories, etc).
 * Extend the driver to:
   * Support waveform tracing,
   * Interface with testbench frameworks,
   * Derive all combinational signal from traced sequential state.

## FPGA Synthesis Results

Development of Nexus has used a Xilinx Artix-7 XC7A200T FPGA as a target device,
aiming to support at least a 10x10 mesh with 2 simulated memories. Each node in
the mesh has been configured with 32 inputs, 32 outputs, and 16 working registers.
A PCIe XDMA instance has been used to support high-speed communication with a host,
and timing has been met at 200 MHz for the mesh (125 MHz for the PCIe core).

The top-level utilisation report for this configuration is shown below:

| Design Unit  | LUTs           | Slice Registers | F7 Muxes     | F8 Muxes   | Block RAMs   |
|--------------|----------------|-----------------|--------------|------------|--------------|
| nexus        | 53720 (40.1 %) | 44931 (16.7 %)  | 1764 (2.6 %) | 10 (~0 %)  | 102 (27.9 %) |
| - nx_control | 7297   (5.4 %) | 376    (0.1 %)  | 0            | 0          | 2    (0.5 %) |
| - nx_mesh    | 46423 (34.7 %) | 44555 (16.6 %)  | 1764 (2.6 %) | 10 (0.2 %) | 100 (27.4 %) |

**NOTE:** Percentages indicate proportion of total resources on an Artix-7 200T.

The implementation utilisation report the largest node within the mesh is as follows:

| Design Unit             | LUTs | Slice Registers | F7 Muxes | F8 Muxes | Block RAMs |
|-------------------------|------|-----------------|----------|----------|------------|
| nx_node                 | 522  | 459             | 15       | 0        | 1          |
| - nx_node_core          | 172  | 73              | 0        | 0        | 0          |
| - nx_node_control       | 129  | 170             | 12       | 0        | 0          |
| - nx_stream_distributor | 93   | 68              | 0        | 0        | 0          |
| - nx_stream_arbiter [1] | 91   | 33              | 0        | 0        | 0          |
| - nx_node_decoder       | 20   | 69              | 0        | 0        | 0          |
| - nx_node_store         | 9    | 15              | 3        | 0        | 1          |
| - nx_stream_arbiter [2] | 8    | 30              | 0        | 0        | 0          |

**NOTE:** The mesh is largely homogenous - but resource utilisation does vary
between nodes for a number of reasons, for example a node at the corner of the
mesh can be missing up to two messaging interfaces which lowers the complexity
of the stream components. The smallest node in the mesh has only 436 LUTs (around
84% of the size).
