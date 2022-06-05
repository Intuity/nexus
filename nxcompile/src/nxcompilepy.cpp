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

#include "nxdump_stats.hpp"
#include "nxconstant.hpp"
#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxlogging.hpp"
#include "nxmodule.hpp"
#include "nxopt_propagate.hpp"
#include "nxopt_prune.hpp"
#include "nxparser.hpp"
#include "nxport.hpp"
#include "nxsignal.hpp"

namespace py = pybind11;
using namespace Nexus;

PYBIND11_MODULE(nxcompile, m) {

    // Expose enumerations
    py::enum_<NXSignal::nxsignal_type_t>(m, "nxsignal_type_t")
        .value("UNKNOWN",  NXSignal::nxsignal_type_t::UNKNOWN )
        .value("CONSTANT", NXSignal::nxsignal_type_t::CONSTANT)
        .value("WIRE",     NXSignal::nxsignal_type_t::WIRE    )
        .value("GATE",     NXSignal::nxsignal_type_t::GATE    )
        .value("FLOP",     NXSignal::nxsignal_type_t::FLOP    )
        .value("PORT",     NXSignal::nxsignal_type_t::PORT    );

    py::enum_<NXPort::nxport_type_t>(m, "nxport_type_t")
        .value("UNKNOWN", NXPort::nxport_type_t::UNKNOWN)
        .value("INPUT",   NXPort::nxport_type_t::INPUT  )
        .value("OUTPUT",  NXPort::nxport_type_t::OUTPUT );

    py::enum_<NXGate::nxgate_op_t>(m, "nxgate_op_t")
        .value("UNKNOWN", NXGate::nxgate_op_t::UNKNOWN)
        .value("ASSIGN",  NXGate::nxgate_op_t::ASSIGN )
        .value("AND",     NXGate::nxgate_op_t::AND    )
        .value("OR",      NXGate::nxgate_op_t::OR     )
        .value("NOT",     NXGate::nxgate_op_t::NOT    )
        .value("XOR",     NXGate::nxgate_op_t::XOR    )
        .value("COND",    NXGate::nxgate_op_t::COND   );

    // Expose classes
    py::class_<NXParser, std::shared_ptr<NXParser>>(m, "NXParser")
        .def_static("parse_from_file", &NXParser::parse_from_file);

    py::class_<NXModule, std::shared_ptr<NXModule>>(m, "NXModule")
        .def(py::init<
              std::string // name
        >())
        // Methods
        .def("add_port",   &NXModule::add_port  )
        .def("add_gate",   &NXModule::add_gate  )
        .def("add_flop",   &NXModule::add_flop  )
        .def("add_wire",   &NXModule::add_wire  )
        .def("get_signal", &NXModule::get_signal)
        // Members
        .def_readwrite("name",    &NXModule::m_name   )
        .def_readwrite("ports",   &NXModule::m_ports  )
        .def_readwrite("gates",   &NXModule::m_gates  )
        .def_readwrite("flops",   &NXModule::m_flops  )
        .def_readwrite("wires",   &NXModule::m_wires  )
        .def_readwrite("signals", &NXModule::m_signals);

    py::class_<NXSignal, std::shared_ptr<NXSignal>>(m, "NXSignal")
        .def(py::init<
              std::string               // name
            , NXSignal::nxsignal_type_t // type
            , int                       // max_inputs
            , int                       // max_outputs
        >())
        // Methods
        .def("is_type",    &NXSignal::is_type   )
        .def("set_clock",  &NXSignal::set_clock )
        .def("set_reset",  &NXSignal::set_reset )
        .def("add_input",  &NXSignal::add_input )
        .def("add_output", &NXSignal::add_output)
        // Members
        .def_readwrite("name",        &NXSignal::m_name)
        .def_readwrite("type",        &NXSignal::m_type)
        .def_readwrite("max_inputs",  &NXSignal::m_max_inputs)
        .def_readwrite("max_outputs", &NXSignal::m_max_outputs)
        .def_readwrite("clock",       &NXSignal::m_clock)
        .def_readwrite("reset",       &NXSignal::m_reset)
        .def_readwrite("inputs",      &NXSignal::m_inputs)
        .def_readwrite("outputs",     &NXSignal::m_outputs);

    py::class_<NXConstant, NXSignal, std::shared_ptr<NXConstant>>(m, "NXConstant")
        .def(py::init<
              unsigned int // value
            , int          // width
        >())
        // Methods
        .def("from_signal", &NXConstant::from_signal)
        // Members
        .def_readwrite("value", &NXConstant::m_value)
        .def_readwrite("width", &NXConstant::m_width);

    py::class_<NXFlop, NXSignal, std::shared_ptr<NXFlop>>(m, "NXFlop")
        .def(py::init<
              std::string // name
        >())
        .def("from_signal", &NXFlop::from_signal)
        .def_readwrite("rst_val", &NXFlop::m_rst_val);

    py::class_<NXGate, NXSignal, std::shared_ptr<NXGate>>(m, "NXGate")
        .def(py::init<NXGate::nxgate_op_t>())
        .def("from_signal", &NXGate::from_signal)
        .def_readwrite("op", &NXGate::m_op);

    py::class_<NXPort, NXSignal, std::shared_ptr<NXPort>>(m, "NXPort")
        .def(py::init<
              std::string           // name
            , NXPort::nxport_type_t // port_type
            , int                   // max_inputs
            , int                   // max_outputs
        >())
        .def("from_signal",  &NXPort::from_signal )
        .def("is_port_type", &NXPort::is_port_type)
        .def_readwrite("port_type", &NXPort::m_port_type);

    py::class_<NXPortIn, NXPort, std::shared_ptr<NXPortIn>>(m, "NXPortIn")
        .def(py::init<
              std::string // name
        >())
        .def("from_port", &NXPortIn::from_port);

    py::class_<NXPortOut, NXPort, std::shared_ptr<NXPortOut>>(m, "NXPortOut")
        .def(py::init<
              std::string // name
        >())
        .def("from_port", &NXPortOut::from_port);

    // Expose functions
    m.def("dump_rtl_stats",     &dump_rtl_stats    );
    m.def("optimise_prune",     &optimise_prune    );
    m.def("optimise_propagate", &optimise_propagate);
    m.def("setup_logging",      &setup_logging     );

}
