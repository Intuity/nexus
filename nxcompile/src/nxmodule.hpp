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

#include <algorithm>
#include <assert.h>
#include <map>
#include <stdint.h>
#include <vector>

#include <plog/Log.h>

#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxport.hpp"

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
            m_signals[port->m_name] = std::static_pointer_cast<NXSignal>(port);
        }

        void add_gate ( std::shared_ptr<NXGate> gate )
        {
            m_gates.push_back(gate);
            m_signals[gate->m_name] = std::static_pointer_cast<NXSignal>(gate);
        }

        void add_flop ( std::shared_ptr<NXFlop> flop )
        {
            m_flops.push_back(flop);
            m_signals[flop->m_name] = std::static_pointer_cast<NXSignal>(flop);
        }

        void add_wire ( std::shared_ptr<NXSignal> wire )
        {
            m_wires.push_back(wire);
            m_signals[wire->m_name] = std::static_pointer_cast<NXSignal>(wire);
        }

        bool has_signal ( std::string name )
        {
            return m_signals.find(name) != m_signals.end();
        }

        std::shared_ptr<NXSignal> get_signal ( std::string name )
        {
            if (!has_signal(name)) {
                PLOGE << "Failed to locate signal " << name;
                assert(!"Cannot locate named signal");
            }
            assert(has_signal(name));
            return m_signals[name];
        }

        void drop_signal ( std::shared_ptr<NXSignal> signal ) {
            // Drop from the relevant list
            switch (signal->m_type) {
                case NXSignal::PORT: {
                    auto pos = std::find(m_ports.begin(), m_ports.end(), NXPort::from_signal(signal));
                    assert(pos != m_ports.end());
                    m_ports.erase(pos);
                    break;
                }
                case NXSignal::GATE: {
                    auto pos = std::find(m_gates.begin(), m_gates.end(), NXGate::from_signal(signal));
                    assert(pos != m_gates.end());
                    m_gates.erase(pos);
                    break;
                }
                case NXSignal::FLOP: {
                    auto pos = std::find(m_flops.begin(), m_flops.end(), NXFlop::from_signal(signal));
                    assert(pos != m_flops.end());
                    m_flops.erase(pos);
                    break;
                }
                case NXSignal::WIRE: {
                    auto pos = std::find(m_wires.begin(), m_wires.end(), signal);
                    assert(pos != m_wires.end());
                    m_wires.erase(pos);
                    break;
                }
                default:
                    assert(!"Unknown signal type");
                    break;
            }
            // Drop from the signals map
            assert(has_signal(signal->m_name));
            m_signals.erase(signal->m_name);
        }

        // =====================================================================
        // Members
        // =====================================================================

        std::string                                        m_name;
        std::vector< std::shared_ptr<NXPort> >             m_ports;
        std::vector< std::shared_ptr<NXGate> >             m_gates;
        std::vector< std::shared_ptr<NXFlop> >             m_flops;
        std::vector< std::shared_ptr<NXSignal> >           m_wires;
        std::map< std::string, std::shared_ptr<NXSignal> > m_signals;

    };

}

#endif // __NXMODULE_HPP__
