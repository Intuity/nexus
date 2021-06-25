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

import click
import simpy

from .base import Base
from .capture import Capture
from .manager import Manager
from .mesh import Mesh
from .node import Direction
from .pipe import Pipe

@click.command()
# Simulation options
@click.option("--cycles", type=int, default=100,           help="How many cycles to run for")
@click.option("--vcd",    type=click.Path(dir_okay=False), help="Path for recorded VCD")
# Mesh configuration
@click.option("-r", "--rows", type=int, default=8, help="Rows in the mesh")
@click.option("-c", "--cols", type=int, default=8, help="Columns in the mesh")
# Node configuration
@click.option("--node-inputs",    type=int, default=8,  help="Inputs per node")
@click.option("--node-outputs",   type=int, default=8,  help="Outputs per node")
@click.option("--node-registers", type=int, default=8,  help="Working registers")
# Verbosity controls
@click.option("--quiet", count=True, help="Only show warning & error messages")
@click.option("--debug", count=True, help="Enable debug messages")
@click.option("--log",   type=click.Path(file_okay=True, dir_okay=False), help="Output log path")
# Debug controls
@click.option("--break-on-idle", count=True, help="Enter debug when mesh is idle")
# Simulation setup
@click.argument("design", type=click.File("r"))
def main(
    # Simulation options
    cycles, vcd,
    # Mesh configuration
    rows, cols,
    # Node configuration
    node_inputs, node_outputs, node_registers,
    # Verbosity controls
    quiet, debug, log,
    # Debug controls
    break_on_idle,
    # Simulation setup
    design,
):
    """ Architectural model of the Nexus accelerator

    Arguments:

        DESIGN: Path to the compiled design to load and execute.
    """
    # Create a simulation environment
    env = simpy.Environment()
    # Setup verbosity
    Base.setup_log(env, {
        (True,  True ): "INFO",
        (True,  False): "WARN",
        (False, True ): "DEBUG",
        (False, False): "INFO",
    }[quiet, debug], log)
    # Create a mesh
    mesh = Mesh(env, rows, cols, nd_prms={
        "inputs"   : node_inputs,
        "outputs"  : node_outputs,
        "registers": node_registers,
    })
    # Create a manager
    manager = Manager(env, mesh, cycles=cycles, break_on_idle=break_on_idle)
    mesh[0, 0].inbound[Direction.NORTH] = manager.outbound
    out_lkp = manager.load(design)
    # Create a capture node
    capture = Capture(env, mesh, cols, out_lkp, debug=debug)
    for col, node in enumerate(mesh.nodes[rows-1]):
        capture.inbound[col] = node.outbound[Direction.SOUTH] = Pipe(env, 1, 1)
    manager.add_observer(capture.tick)
    # Run the simulation
    env.run(until=manager.complete)
    # Optionally write out VCD
    if vcd: capture.write_to_vcd(vcd)

if __name__ == "__main__":
    main(prog_name="nxmodel")
