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

#include <map>
#include <memory>

#include <plog/Log.h>

#include "nxopt_prune.hpp"

using namespace Nexus;

// optimise_prune
// Prune dead signals, flops, gates from a module that are not driven or do not
// drive any logic.
//
void Nexus::optimise_prune ( std::shared_ptr<NXModule> module )
{
    // Take a copy of the map to avoid mutation while iterating
    std::map< std::string, std::shared_ptr<NXSignal> > sig_map(module->m_signals);
    // Search for items to drop
    for (auto sig_pair : sig_map) {
        auto signal = sig_pair.second;
        if (signal->m_inputs.size() == 0 && signal->m_outputs.size() == 0) {
            module->drop_signal(signal);
        }
    }
}
