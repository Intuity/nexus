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

from pathlib import Path

from nxfastmodel import Nexus, NXMesh, NXNode, NXLoader

# Create an instance of the model
print("# Creating a 6x6 mesh")
instance = Nexus(6, 6)
print(f"# Instance reports {instance.get_rows()}x{instance.get_columns()}")

# Extract the mesh
print("# Extracting NXMesh from model")
inst_mesh = instance.get_mesh()
assert isinstance(inst_mesh, NXMesh)

# Extract a node
print("# Extracting node 0, 2")
inst_node = inst_mesh.get_node(0, 2)
assert isinstance(inst_node, NXNode)

# Load a model into the mesh
NXLoader(instance, (Path(__file__).parent / "design.json").as_posix())

# Run the mesh for 10,000 cycles
instance.run(10000)

# Pull the first few outputs
for idx in range(10):
    summary = instance.pop_output()
    print(f"{idx:02d} : {summary}")

# Read back the current input state from node
print(f"# Current inputs : {inst_node.get_current_inputs()}")
print(f"# Next inputs    : {inst_node.get_next_inputs()}")
print(f"# Current outputs: {inst_node.get_current_outputs()}")

# All good
print("# All done!")
