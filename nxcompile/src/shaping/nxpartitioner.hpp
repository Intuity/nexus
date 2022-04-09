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

#ifndef __NXPARTITION_HPP__
#define __NXPARTITION_HPP__

#include <assert.h>
#include <list>
#include <memory>
#include <set>
#include <sstream>
#include <vector>

#include "nxflop.hpp"
#include "nxgate.hpp"
#include "nxmodule.hpp"

namespace Nexus {

    class NXPartitioner;

    class NXPartition {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXPartition (
              int                            index
            , std::shared_ptr<NXPartitioner> partitioner
        ) : m_index  ( index       )
          , m_parent ( partitioner )
        { }

        // =====================================================================
        // Methods
        // =====================================================================

        void add ( std::shared_ptr<NXFlop> flop )
        {
            flop->set_tag("partition", m_index);
            m_flops.push_back(flop);
        }

        void add ( std::shared_ptr<NXGate> gate )
        {
            gate->set_tag("partition", m_index);
            m_gates.push_back(gate);
        }

        void add ( std::shared_ptr<NXSignal> signal )
        {
            switch (signal->m_type) {
                case NXSignal::GATE:
                    add(NXGate::from_signal(signal));
                    break;
                case NXSignal::FLOP:
                    add(NXFlop::from_signal(signal));
                    break;
                default: assert(!"Unsupported signal type");
            }
        }

        void remove ( std::shared_ptr<NXFlop> flop )
        {
            m_flops.remove(flop);
        }

        void remove ( std::shared_ptr<NXGate> gate )
        {
            m_gates.remove(gate);
        }

        void remove ( std::shared_ptr<NXSignal> signal )
        {
            switch (signal->m_type) {
                case NXSignal::GATE:
                    remove(NXGate::from_signal(signal));
                    break;
                case NXSignal::FLOP:
                    remove(NXFlop::from_signal(signal));
                    break;
                default: assert(!"Unsupported signal type");
            }
        }

        std::string announce ( void )
        {
            unsigned int req_ins  = required_inputs().size();
            unsigned int req_outs = required_outputs().size();
            std::stringstream ss;
            ss << "Partition " << std::dec << m_index << " has "
               << m_flops.size() << " flops and " << m_gates.size()
               << " gates and needs " << req_ins << " inputs and " << req_outs
               << " outputs (total: " << (req_ins + req_outs) << ")";
            return ss.str();
        }

        static std::shared_ptr<NXSignal> chase_to_source (
            std::shared_ptr<NXSignal> ptr
        );

        static std::vector< std::shared_ptr<NXSignal> > chase_to_targets (
              std::shared_ptr<NXSignal> ptr
            , bool                      thru_gates=false
        );

        std::list< std::shared_ptr<NXSignal> > all_flops_and_gates ( void );

        std::set<std::shared_ptr<NXSignal>> trace_inputs (
            std::shared_ptr<NXSignal> root
        );

        std::set<std::shared_ptr<NXSignal>> trace_outputs (
            std::shared_ptr<NXSignal> root
        );

        std::map<std::shared_ptr<NXSignal>, unsigned int> required_inputs ( void );

        std::map<std::shared_ptr<NXSignal>, unsigned int> required_outputs ( void );

        bool fits ( unsigned int node_inputs, unsigned int node_outputs );

        // =====================================================================
        // Members
        // =====================================================================

        int                                  m_index;
        std::weak_ptr<NXPartitioner>         m_parent;
        std::list< std::shared_ptr<NXFlop> > m_flops;
        std::list< std::shared_ptr<NXGate> > m_gates;

    };

    class NXPartitioner : public std::enable_shared_from_this<NXPartitioner>
    {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXPartitioner (
              std::shared_ptr<NXModule> module
            , unsigned int              node_inputs
            , unsigned int              node_outputs
        ) : m_module       ( module       )
          , m_node_inputs  ( node_inputs  )
          , m_node_outputs ( node_outputs )
        { }

        // =====================================================================
        // Methods
        // =====================================================================

        void run ( void );

        // =====================================================================
        // Members
        // =====================================================================

        std::shared_ptr<NXModule>                 m_module;
        unsigned int                              m_node_inputs;
        unsigned int                              m_node_outputs;
        std::list< std::shared_ptr<NXPartition> > m_partitions;

    };

}

#endif // __NXPARTITION_HPP__
