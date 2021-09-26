// Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <pybind11/pybind11.h>

#include "nexus.hpp"

namespace py = pybind11;

using namespace NXModel;

PYBIND11_MODULE(nxfastmodel, m) {
    py::class_<Nexus>(m, "Nexus")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_rows",    &Nexus::get_rows   )
        .def("get_columns", &Nexus::get_columns)
        .def("get_mesh",    &Nexus::get_mesh   )
        .def("run",         &Nexus::run        )
        .def("dump_vcd",    &Nexus::dump_vcd   );

    py::class_<NXMesh>(m, "NXMesh")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_node", &NXMesh::get_node)
        .def("is_idle",  &NXMesh::is_idle )
        .def("step",     &NXMesh::step    );

    py::class_<NXNode>(m, "NXNode")
        .def(py::init<uint32_t, uint32_t>());
}
