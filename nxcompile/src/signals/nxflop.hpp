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

#ifndef __NXFLOP_HPP__
#define __NXFLOP_HPP__

namespace Nexus {

    class NXFlop : public NXSignal {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXFlop ( std::string name );

        // =====================================================================
        // Methods
        // =====================================================================

        static std::shared_ptr<NXFlop> from_signal ( std::shared_ptr<NXSignal> signal )
        {
            return NXSignal::as<NXFlop>(signal);
        }

        // =====================================================================
        // Members
        // =====================================================================

        std::shared_ptr<NXSignal> m_rst_val;

    };

}

#endif // __NXFLOP_HPP__
