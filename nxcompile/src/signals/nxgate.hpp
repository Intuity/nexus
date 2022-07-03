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

#include <initializer_list>
#include <memory>
#include <vector>

#include "nxsignal.hpp"

#ifndef __NXGATE_HPP__
#define __NXGATE_HPP__

namespace Nexus {

    class NXGate : public NXSignal {
    public:

        // =====================================================================
        // Typedefs
        // =====================================================================

        typedef enum {
              UNKNOWN
            , ASSIGN
            , AND
            , OR
            , NOT
            , XOR
            , COND
        } nxgate_op_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXGate ( nxgate_op_t op );

        // =====================================================================
        // Methods
        // =====================================================================

        static std::shared_ptr<NXGate> from_signal ( std::shared_ptr<NXSignal> signal )
        {
            return NXSignal::as<NXGate>(signal);
        }


        static std::string op_to_str ( nxgate_op_t op )
        {
            switch (op) {
                case UNKNOWN:
                    return "UNKNOWN";
                case ASSIGN:
                    return "ASSIGN";
                case AND:
                    return "AND";
                case OR:
                    return "OR";
                case NOT:
                    return "NOT";
                case XOR:
                    return "XOR";
                case COND:
                    return "COND";
            }
            return "UNSUPPORTED";
        }

        // =====================================================================
        // Members
        // =====================================================================

        nxgate_op_t m_op;

    };

}

#endif // __NXGATE_HPP__
