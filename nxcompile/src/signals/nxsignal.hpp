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

#include <assert.h>
#include <memory>
#include <string>
#include <vector>

#ifndef __NXSIGNAL_HPP__
#define __NXSIGNAL_HPP__

namespace Nexus {
    class NXSignal {
    public:

        // =====================================================================
        // Definitions
        // =====================================================================

        typedef enum {
              UNKNOWN
            , CONSTANT
            , WIRE
            , GATE
            , FLOP
            , PORT
        } nxsignal_type_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXSignal (
              std::string     name
            , nxsignal_type_t type
            , int             max_inputs  = -1
            , int             max_outputs = -1
        ) : m_name        ( name        )
          , m_type        ( type        )
          , m_max_inputs  ( max_inputs  )
          , m_max_outputs ( max_outputs )
        { }

        // =====================================================================
        // Methods
        // =====================================================================

        bool is_type ( nxsignal_type_t type )
        {
            return type == m_type;
        }

        void set_clock ( std::shared_ptr<NXSignal> clock )
        {
            m_clock = clock;
        }

        void set_reset ( std::shared_ptr<NXSignal> reset )
        {
            m_reset = reset;
        }

        void add_input ( std::shared_ptr<NXSignal> signal )
        {
            assert(m_max_inputs < 0 || (m_inputs.size() < m_max_inputs));
            m_inputs.push_back(signal);
        }

        void add_output ( std::shared_ptr<NXSignal> signal )
        {
            assert(m_max_outputs < 0 || (m_outputs.size() < m_max_outputs));
            m_outputs.push_back(signal);
        }

        template<typename T> T & as ( )
        {
            return *static_cast<T *>(this);
        }

        // =====================================================================
        // Members
        // =====================================================================

        std::string                            m_name;
        nxsignal_type_t                        m_type;
        int                                    m_max_inputs;
        int                                    m_max_outputs;
        std::shared_ptr<NXSignal>              m_clock;
        std::shared_ptr<NXSignal>              m_reset;
        std::vector<std::shared_ptr<NXSignal>> m_inputs;
        std::vector<std::shared_ptr<NXSignal>> m_outputs;

    };

}

#endif // __NXSIGNAL_HPP__
