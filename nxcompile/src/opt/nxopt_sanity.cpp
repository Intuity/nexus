// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
#include <plog/Log.h>

#include "nxopt_sanity.hpp"

using namespace Nexus;

// optimise_sanity
// For every gate in the design, check that forward and backwards links are
// correctly connected.
//
void Nexus::optimise_sanity(
      std::shared_ptr<NXModule> module
    , bool allow_const_terms /* = true */
) {
    PLOGI << "Performing sanity check on all signals";
    bool all_ok = true;
    for (auto pair : module->m_signals) {

        auto signal = pair.second;

        // Check each input includes this signal as an output
        for (auto input : signal->m_inputs) {
            if (input == signal) {
                continue;
            } else if (!input->has_output(signal)) {
                PLOGE << "Signal " << input->m_name << " is missing an output "
                      << signal->m_name;
                all_ok = false;
            }
        }

        // Check each output includes this signal as an input
        for (auto output : signal->m_outputs) {
            if (output == signal) {
                continue;
            } else if (
                output->m_type == NXSignal::FLOP && (
                    NXFlop::from_signal(output)->m_clock == signal ||
                    NXFlop::from_signal(output)->m_reset == signal
                )
            ) {
                continue;
            } else if (!output->has_input(signal)) {
                PLOGE << "Signal " << output->m_name << " is missing an input "
                      << signal->m_name;
                all_ok = false;
            }
        }

        // For any gates, check that no input terms are constant
        if (!allow_const_terms && signal->m_type == NXSignal::GATE) {
            auto gate = NXGate::from_signal(signal);
            for (auto input : gate->m_inputs) {
                if (input->m_type == NXSignal::CONSTANT) {
                    PLOGE << "Gate '" << gate->m_name << "' with operation "
                          << NXGate::op_to_str(gate->m_op) << " with "
                          << gate->m_inputs.size() << " inputs is driven by '"
                          << input->m_name << "' which is constant";
                    all_ok = false;
                }
            }
        }

    }
    assert(all_ok);
}
