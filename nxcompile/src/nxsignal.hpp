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
#include <vector>

#ifndef __NXSIGNAL_HPP__
#define __NXSIGNAL_HPP__

namespace Nexus {

    class NXSignal {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXSignal () { }

        // =====================================================================
        // Methods
        // =====================================================================

        void set_clock  ( std::shared_ptr<NXSignal> clock  ) { m_clock = clock; }
        void set_reset  ( std::shared_ptr<NXSignal> reset  ) { m_reset = reset; }
        void add_output ( std::shared_ptr<NXSignal> signal ) { m_outputs.push_back(signal); }

    private:

        // =====================================================================
        // Members
        // =====================================================================

        std::shared_ptr<NXSignal>              m_clock;
        std::shared_ptr<NXSignal>              m_reset;
        std::vector<std::shared_ptr<NXSignal>> m_outputs;

    };

}

#endif // __NXSIGNAL_HPP__
