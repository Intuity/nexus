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

from nxfastmodel import Nexus, NXMesh, NXNode

# Create an instance of the model
print("# Creating a 10x10 mesh")
instance = Nexus(10, 10)
print(f"# Instance reports {instance.get_rows()}x{instance.get_columns()}")

# Extract the mesh
print("# Extracting NXMesh from model")
inst_mesh = instance.get_mesh()
assert isinstance(inst_mesh, NXMesh)

# Extract a node
print("# Extracting node")
inst_node = inst_mesh.get_node(2, 2)
assert isinstance(inst_node, NXNode)

# All good
print("# All done!")
