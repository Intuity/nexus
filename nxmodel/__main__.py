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

from .base import Base, Verbosity
from .manager import Manager
from .mesh import Mesh

@click.command()
# Mesh configuration
@click.option("-r", "--rows", type=int, default=8,  help="Rows in the mesh")
@click.option("-c", "--cols", type=int, default=8,  help="Columns in the mesh")
# Node configuration
@click.option("--node-inputs",    type=int, default=8,  help="Inputs per node")
@click.option("--node-outputs",   type=int, default=8,  help="Outputs per node")
@click.option("--node-registers", type=int, default=8,  help="Working registers")
@click.option("--node-slots",     type=int, default=16, help="Max instructions per node")
# Verbosity controls
@click.option("--quiet", count=True, help="Only show warning & error messages")
@click.option("--debug", count=True, help="Enable debug messages")
# Simulation setup
@click.argument("design", type=click.File("r"))
def main(
    # Mesh configuration
    rows, cols, node_inputs, node_outputs, node_registers, node_slots,
    # Verbosity controls
    quiet, debug,
    # Simulation setup
    design,
):
    """ Architectural model of the Nexus accelerator

    Arguments:

        DESIGN: Path to the compiled design to load and execute.
    """
    # Setup verbosity
    if   quiet: Base.set_verbosity(Verbosity.WARN )
    elif debug: Base.set_verbosity(Verbosity.DEBUG)
    else      : Base.set_verbosity(Verbosity.INFO )
    # Create a simulation environment
    env = simpy.Environment()
    # Create a mesh
    mesh = Mesh(env, rows, cols, nd_prms={
        "inputs"   : node_inputs,
        "outputs"  : node_outputs,
        "registers": node_registers,
        "max_ops"  : node_slots,
    })
    # Create a manager
    manager = Manager(env, mesh)
    manager.load(design)
    # Run the simulation
    env.run()

if __name__ == "__main__":
    main(prog_name="nxmodel")
