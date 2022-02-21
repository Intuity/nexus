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
              NX_OP_AND
            , NX_OP_OR
            , NX_OP_NOT
            , NX_OP_XOR
        } nx_operation_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXGate (
              nx_operation_t op
            , std::initializer_list<std::shared_ptr<NXSignal>> inputs
        );

    private:

        // =====================================================================
        // Members
        // =====================================================================

        nx_operation_t                         m_op;
        std::vector<std::shared_ptr<NXSignal>> m_inputs;

    };

}

#endif // __NXGATE_HPP__
