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

#include "nxcompile.hpp"
#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxsignal.hpp"

namespace py = pybind11;
using namespace Nexus;

PYBIND11_MODULE(nxcompile, m) {

    // Expose classes
    py::class_<NXCompile, std::shared_ptr<NXCompile>>(m, "NXCompile")
        .def(py::init<>());

    py::class_<NXFlop, std::shared_ptr<NXFlop>>(m, "NXFlop")
        .def(py::init<std::shared_ptr<NXSignal>>());

    py::class_<NXGate, std::shared_ptr<NXGate>>(m, "NXGate")
        .def(py::init<
            NXGate::nx_operation_t,
            std::initializer_list<std::shared_ptr<NXSignal>>
        >());

    py::class_<NXSignal, std::shared_ptr<NXSignal>>(m, "NXSignal")
        .def(py::init<>());

}
