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

#include "nxmodule.hpp"
#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxport.hpp"
#include "nxsignal.hpp"
#include "nxwire.hpp"

namespace py = pybind11;
using namespace Nexus;

PYBIND11_MODULE(nxcompile, m) {

    // Expose classes
    py::class_<NXModule, std::shared_ptr<NXModule>>(m, "NXModule")
        .def(py::init<
              std::string // name
        >());

    py::class_<NXFlop, std::shared_ptr<NXFlop>>(m, "NXFlop")
        .def(py::init<
              std::string               // name
            , std::shared_ptr<NXSignal> // clk
            , std::shared_ptr<NXSignal> // rst
        >());

    py::class_<NXGate, std::shared_ptr<NXGate>>(m, "NXGate")
        .def(py::init<NXGate::nxgate_op_t>());

    py::class_<NXPort, std::shared_ptr<NXPort>>(m, "NXPort")
        .def(py::init<
              std::string           // name
            , NXPort::nxport_type_t // port_type
            , int                   // max_inputs
            , int                   // max_outputs
        >());

    py::class_<NXPortIn, std::shared_ptr<NXPortIn>>(m, "NXPortIn")
        .def(py::init<
              std::string // name
        >());

    py::class_<NXPortOut, std::shared_ptr<NXPortOut>>(m, "NXPortOut")
        .def(py::init<
              std::string // name
        >());

    py::class_<NXSignal, std::shared_ptr<NXSignal>>(m, "NXSignal")
        .def(py::init<
              std::string               // name
            , NXSignal::nxsignal_type_t // type
            , int                       // max_inputs
            , int                       // max_outputs
        >());

    py::class_<NXWire, std::shared_ptr<NXWire>>(m, "NXWire")
        .def(py::init<
              std::string // name
        >());

}
