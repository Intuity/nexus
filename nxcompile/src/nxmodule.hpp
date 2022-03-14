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

#include <map>
#include <stdint.h>
#include <vector>

#include <plog/Log.h>

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

        void add_port ( std::shared_ptr<NXPort> port )
        {
            m_ports.push_back(port);
            m_signals[port->m_name] = port;
        }

        void add_gate ( std::shared_ptr<NXGate> gate )
        {
            m_gates.push_back(gate);
            m_signals[gate->m_name] = gate;
            PLOGI << "Adding gate " << std::dec << m_gates.size();
        }

        void add_flop ( std::shared_ptr<NXFlop> flop )
        {
            m_flops.push_back(flop);
            m_signals[flop->m_name] = flop;
        }

        void add_wire ( std::shared_ptr<NXWire> wire )
        {
            m_wires.push_back(wire);
            m_signals[wire->m_name] = wire;
        }

        std::shared_ptr<NXSignal> get_signal ( std::string name )
        {
            return m_signals[name];
        }


    private:

        // =====================================================================
        // Members
        // =====================================================================

        std::string                                        m_name;
        std::vector< std::shared_ptr<NXPort> >             m_ports;
        std::vector< std::shared_ptr<NXGate> >             m_gates;
        std::vector< std::shared_ptr<NXFlop> >             m_flops;
        std::vector< std::shared_ptr<NXWire> >             m_wires;
        std::map< std::string, std::shared_ptr<NXSignal> > m_signals;

    };

}

#endif // __NXMODULE_HPP__
