// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
#include "nxlogging.hpp"

namespace py = pybind11;

PYBIND11_MODULE(nxmodel, m) {
    // Expose enumerations
    py::enum_<NXConstants::direction_t>(m, "direction_t")
        .value("NORTH", NXConstants::DIRECTION_NORTH)
        .value("EAST",  NXConstants::DIRECTION_EAST )
        .value("SOUTH", NXConstants::DIRECTION_SOUTH)
        .value("WEST",  NXConstants::DIRECTION_WEST )
        .export_values();

    // Expose structs
    py::class_<NXConstants::node_id_t>(m, "node_id_t")
        .def(py::init([]() { NXConstants::node_id_t _; return _; }));
    py::class_<NXConstants::node_load_t>(m, "node_load_t")
        .def(py::init([]() { NXConstants::node_load_t _; return _; }));
    py::class_<NXConstants::node_signal_t>(m, "node_signal_t")
        .def(py::init([]() { NXConstants::node_signal_t _; return _; }));
    py::class_<NXConstants::node_raw_t>(m, "node_raw_t")
        .def(py::init([]() { NXConstants::node_raw_t _; return _; }));

    // Expose log control functions
    m.def("setup_logging", &Nexus::setup_logging);

    // Expose packing functions
    m.def("pack_node_load", [](NXConstants::node_load_t msg) -> uint32_t {
        uint32_t raw = 0;
        NXConstants::pack_node_load(msg, (uint8_t *)&raw);
        return raw;
    });
    m.def("pack_node_signal", [](NXConstants::node_signal_t msg) -> uint32_t {
        uint32_t raw = 0;
        NXConstants::pack_node_signal(msg, (uint8_t *)&raw);
        return raw;
    });
    m.def("pack_node_raw", [](NXConstants::node_raw_t msg) -> uint32_t {
        uint32_t raw = 0;
        NXConstants::pack_node_raw(msg, (uint8_t *)&raw);
        return raw;
    });

    // Expose unpacking functions
    m.def("unpack_node_load", [](uint32_t raw) -> NXConstants::node_load_t {
        return NXConstants::unpack_node_load((uint8_t *)&raw);
    });
    m.def("unpack_node_signal", [](uint32_t raw) -> NXConstants::node_signal_t {
        return NXConstants::unpack_node_signal((uint8_t *)&raw);
    });
    m.def("unpack_node_raw", [](uint32_t raw) -> NXConstants::node_raw_t {
        return NXConstants::unpack_node_raw((uint8_t *)&raw);
    });

    // Expose classes
    py::class_<NXModel::Nexus, std::shared_ptr<NXModel::Nexus>>(m, "Nexus")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_rows",            &NXModel::Nexus::get_rows           )
        .def("get_columns",         &NXModel::Nexus::get_columns        )
        .def("get_mesh",            &NXModel::Nexus::get_mesh           )
        .def("get_ingress",         &NXModel::Nexus::get_ingress        )
        .def("get_egress",          &NXModel::Nexus::get_egress         )
        .def("run",                 &NXModel::Nexus::run                )
        .def("dump_vcd",            &NXModel::Nexus::dump_vcd           )
        .def("is_output_available", &NXModel::Nexus::is_output_available)
        .def("pop_output",          &NXModel::Nexus::pop_output         );

    py::class_<NXModel::NXMesh, std::shared_ptr<NXModel::NXMesh>>(m, "NXMesh")
        .def(py::init<uint32_t, uint32_t>())
        .def("get_node", static_cast<std::shared_ptr<NXModel::NXNode> (NXModel::NXMesh::*)(NXConstants::node_id_t)>(&NXModel::NXMesh::get_node))
        .def("get_node", static_cast<std::shared_ptr<NXModel::NXNode> (NXModel::NXMesh::*)(uint32_t, uint32_t)>(&NXModel::NXMesh::get_node))
        .def("is_idle",  &NXModel::NXMesh::is_idle )
        .def("step",     &NXModel::NXMesh::step    );

    py::class_<NXModel::NXNode, std::shared_ptr<NXModel::NXNode>>(m, "NXNode")
        .def(py::init<uint8_t, uint8_t, bool>())
        .def("reset",            &NXModel::NXNode::reset           )
        .def("set_node_id",      static_cast<void (NXModel::NXNode::*)(uint8_t, uint8_t)>(&NXModel::NXNode::set_node_id))
        .def("attach",           &NXModel::NXNode::attach          )
        .def("get_pipe",         &NXModel::NXNode::get_pipe        )
        .def("is_idle",          &NXModel::NXNode::is_idle         )
        .def("is_waiting",       &NXModel::NXNode::is_waiting      )
        .def("step",             &NXModel::NXNode::step            )
        .def("get_inst_memory",  &NXModel::NXNode::get_inst_memory )
        .def("get_data_memory",  &NXModel::NXNode::get_data_memory )
        .def("read_data_memory", &NXModel::NXNode::read_data_memory)
        .def("get_pc",           &NXModel::NXNode::get_pc          )
        .def("get_register",     &NXModel::NXNode::get_register    );

    py::class_<NXModel::NXMessagePipe, std::shared_ptr<NXModel::NXMessagePipe>>(m, "NXMessagePipe")
        .def(py::init<>())
        .def("enqueue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_load_t     )>(&NXModel::NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_signal_t   )>(&NXModel::NXMessagePipe::enqueue))
        .def("enqueue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_raw_t      )>(&NXModel::NXMessagePipe::enqueue))
        .def("dequeue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_load_t    &)>(&NXModel::NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_signal_t  &)>(&NXModel::NXMessagePipe::dequeue))
        .def("dequeue", static_cast<void (NXModel::NXMessagePipe::*)(NXConstants::node_raw_t     &)>(&NXModel::NXMessagePipe::dequeue))
        .def("enqueue_raw", &NXModel::NXMessagePipe::enqueue_raw)
        .def("dequeue_raw", &NXModel::NXMessagePipe::dequeue_raw)
        .def("is_idle",     &NXModel::NXMessagePipe::is_idle)
        .def("next_header", &NXModel::NXMessagePipe::next_header)
        .def("next_type",   &NXModel::NXMessagePipe::next_type);

    py::class_<NXModel::NXLoader>(m, "NXLoader")
        .def(py::init<NXModel::Nexus *, std::string>());
}
