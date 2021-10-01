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

#include <filesystem>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "nexus.hpp"
#include "nxloader.hpp"

namespace py = pybind11;

using namespace NXModel;

PYBIND11_MODULE(nxmodel, m) {
    py::class_<Nexus, std::shared_ptr<Nexus>>(m, "Nexus")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_rows",            &Nexus::get_rows           )
        .def("get_columns",         &Nexus::get_columns        )
        .def("get_mesh",            &Nexus::get_mesh           )
        .def("get_ingress",         &Nexus::get_ingress        )
        .def("get_egress",          &Nexus::get_egress         )
        .def("run",                 &Nexus::run                )
        .def("dump_vcd",            &Nexus::dump_vcd           )
        .def("is_output_available", &Nexus::is_output_available)
        .def("pop_output",          &Nexus::pop_output         );

    py::class_<NXMesh, std::shared_ptr<NXMesh>>(m, "NXMesh")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_node", &NXMesh::get_node)
        .def("is_idle",  &NXMesh::is_idle )
        .def("step",     &NXMesh::step    );

    py::class_<NXNode, std::shared_ptr<NXNode>>(m, "NXNode")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_memory",            &NXNode::get_memory           )
        .def("get_instruction_count", &NXNode::get_instruction_count)
        .def("get_output_count",      &NXNode::get_output_count     )
        .def("get_current_inputs",    &NXNode::get_current_inputs   )
        .def("get_next_inputs",       &NXNode::get_next_inputs      )
        .def("get_current_outputs",   &NXNode::get_current_outputs  );

    py::class_<NXMessagePipe, std::shared_ptr<NXMessagePipe>>(m, "NXMessagePipe")
        .def(py::init<>())
        .def("enqueue", static_cast<void (NXMessagePipe::*)(node_load_t      )>(&NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXMessagePipe::*)(node_loopback_t  )>(&NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXMessagePipe::*)(node_signal_t    )>(&NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXMessagePipe::*)(node_control_t   )>(&NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXMessagePipe::*)(node_raw_t       )>(&NXMessagePipe::enqueue))
        .def("dequeue", static_cast<void (NXMessagePipe::*)(node_load_t     &)>(&NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXMessagePipe::*)(node_loopback_t &)>(&NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXMessagePipe::*)(node_signal_t   &)>(&NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXMessagePipe::*)(node_control_t  &)>(&NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXMessagePipe::*)(node_raw_t      &)>(&NXMessagePipe::dequeue))
        .def("enqueue_raw", &NXMessagePipe::enqueue_raw)
        .def("dequeue_raw", &NXMessagePipe::dequeue_raw)
        .def("is_idle",     &NXMessagePipe::is_idle)
        .def("next_header", &NXMessagePipe::next_header)
        .def("next_type",   &NXMessagePipe::next_type);

    py::class_<NXLoader>(m, "NXLoader")
        .def(py::init<Nexus *, std::string>());
}
