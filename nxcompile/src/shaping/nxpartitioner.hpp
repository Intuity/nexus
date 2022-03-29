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

#include <list>
#include <memory>
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

        std::string announce ( void )
        {
            std::stringstream ss;
            ss << "Partition " << std::dec << m_index << " has "
               << m_flops.size() << " flops and " << m_gates.size() << " gates";
            return ss.str();
        }

        std::shared_ptr<NXSignal> chase_to_source (
            std::shared_ptr<NXSignal> ptr
        );

        std::vector< std::shared_ptr<NXSignal> > chase_to_targets (
            std::shared_ptr<NXSignal> ptr
        );

        unsigned int required_inputs (void);

        unsigned int required_outputs (void);

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
