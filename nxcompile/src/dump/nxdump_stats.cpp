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

#include <sstream>

#include "nxdump_stats.hpp"

std::string Nexus::dump_rtl_stats ( std::shared_ptr<NXModule> module )
{
    std::stringstream ss;
    ss << std::endl;
    ss << "======================== [ RTL STATISTICS ] ========================" << std::endl;
    ss << "Top-Level: " << module->m_name << std::endl;
    ss << "Ports    : " << std::dec << module->m_ports.size() << std::endl;
    ss << "Gates    : " << std::dec << module->m_gates.size() << std::endl;
    ss << "Flops    : " << std::dec << module->m_flops.size() << std::endl;
    ss << "Wires    : " << std::dec << module->m_wires.size() << std::endl;
    ss << "====================================================================" << std::endl;
    ss << std::endl;
    return ss.str();
}
