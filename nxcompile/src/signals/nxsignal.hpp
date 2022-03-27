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

#include <algorithm>
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

        // Specialised constructor for derived types
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

        // Simple constructor when used as a simple wire
        NXSignal (
              std::string name
        ) : m_name        ( name )
          , m_type        ( WIRE )
          , m_max_inputs  ( 1    )
          , m_max_outputs ( -1   )
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

        void remove_input ( std::shared_ptr<NXSignal> signal )
        {
            auto pos = std::find(m_inputs.begin(), m_inputs.end(), signal);
            assert(pos != m_inputs.end());
            m_inputs.erase(pos);
        }

        void clear_inputs ( void )
        {
            m_inputs.clear();
        }

        void add_output ( std::shared_ptr<NXSignal> signal )
        {
            assert(m_max_outputs < 0 || (m_outputs.size() < m_max_outputs));
            m_outputs.push_back(signal);
        }

        void remove_output ( std::shared_ptr<NXSignal> signal )
        {
            auto pos = std::find(m_outputs.begin(), m_outputs.end(), signal);
            assert(pos != m_outputs.end());
            m_outputs.erase(pos);
        }

        void clear_outputs ( void )
        {
            m_outputs.clear();
        }

        template<typename T>
        static std::shared_ptr<T> as ( std::shared_ptr<NXSignal> ptr )
        {
            return std::static_pointer_cast<T>(ptr);
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