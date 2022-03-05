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

#include <stdint.h>
#include <vector>

#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxport.hpp"
#include "nxwire.hpp"

#ifndef __NXMODULE_HPP__
#define __NXMODULE_HPP__

namespace Nexus {

    class NXModule {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXModule ( std::string name );

        // =====================================================================
        // Methods
        // =====================================================================

        void add_port ( NXPort * port ) { m_ports.push_back(port); }
        void add_gate ( NXGate * gate ) { m_gates.push_back(gate); }
        void add_flop ( NXFlop * flop ) { m_flops.push_back(flop); }
        void add_wire ( NXWire * wire ) { m_wires.push_back(wire); }

    private:

        // =====================================================================
        // Members
        // =====================================================================

        std::string           m_name;
        std::vector<NXPort *> m_ports;
        std::vector<NXGate *> m_gates;
        std::vector<NXFlop *> m_flops;
        std::vector<NXWire *> m_wires;

    };

}

#endif // __NXMODULE_HPP__
