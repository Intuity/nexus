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

#include <memory>

#include "nxsignal.hpp"

#ifndef __NXPORT_HPP__
#define __NXPORT_HPP__

namespace Nexus {

    class NXPort : public NXSignal {
    public:

        // =====================================================================
        // Definitions
        // =====================================================================

        typedef enum {
              UNKNOWN
            , INPUT
            , OUTPUT
        } nxport_type_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXPort (
              std::string   name
            , nxport_type_t port_type
            , int           max_inputs  = -1
            , int           max_outputs = -1
        );

        // =====================================================================
        // Methods
        // =====================================================================

        bool is_port_type ( nxport_type_t type )
        {
            return type == m_port_type;
        }

        static std::shared_ptr<NXPort> from_signal ( std::shared_ptr<NXSignal> signal )
        {
            return NXSignal::as<NXPort>(signal);
        }

        // =====================================================================
        // Members
        // =====================================================================

        nxport_type_t m_port_type;

    };

    class NXPortIn : public NXPort {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXPortIn (
              std::string name
        ) : NXPort ( name, NXPort::INPUT, 0 )
        { }

        // =====================================================================
        // Methods
        // =====================================================================

        static std::shared_ptr<NXPortIn> from_port ( std::shared_ptr<NXSignal> signal )
        {
            return NXSignal::as<NXPortIn>(signal);
        }

    };

    class NXPortOut : public NXPort {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXPortOut (
              std::string name
        ) : NXPort ( name, NXPort::OUTPUT, -1 )
        { }

        // =====================================================================
        // Methods
        // =====================================================================

        static std::shared_ptr<NXPortOut> from_port ( std::shared_ptr<NXSignal> signal )
        {
            return NXSignal::as<NXPortOut>(signal);
        }

    };

}

#endif // __NXPORT_HPP__
