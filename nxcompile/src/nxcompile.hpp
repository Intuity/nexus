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

#include <stdint.h>
#include <vector>

#include "nxgate.hpp"
#include "nxflop.hpp"

#ifndef __NXCOMPILE_HPP__
#define __NXCOMPILE_HPP__

namespace Nexus {

    class NXCompile {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXCompile ();

    private:

        // =====================================================================
        // Members
        // =====================================================================

        std::vector<NXGate *> m_gates;
        std::vector<NXFlop *> m_flops;

    };

}

#endif // __NXCOMPILE_HPP__
