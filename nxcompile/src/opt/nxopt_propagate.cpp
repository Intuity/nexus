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
#include <map>
#include <memory>

#include <plog/Log.h>

#include "nxconstant.hpp"
#include "nxopt_propagate.hpp"

using namespace Nexus;

// optimise_propagate
// Propagate constants through the design, squashing gates and flops that give a
// fixed result.
//
void Nexus::optimise_propagate ( std::shared_ptr<NXModule> module )
{
    // Iterate until all propagation stops
    unsigned int drop_count = 0;
    unsigned int passes     = 0;
    do {
        // Count passes
        passes += 1;

        // Reset drop count on entry to each iteration
        drop_count = 0;

        // Search through every known gate, propagating constants
        PLOGI << "Starting gate elimination pass " << passes;
        std::vector<std::shared_ptr<NXSignal>> to_drop;
        for (auto gate : module->m_gates) {
            // Run through inputs looking for any 0/1/real variables
            unsigned int num_zero = 0;
            unsigned int num_one  = 0;
            unsigned int num_var  = 0;
            for (auto signal : gate->m_inputs) {
                if (signal->m_type != NXSignal::CONSTANT) {
                    num_var += 1;
                } else {
                    auto constant = NXConstant::from_signal(signal);
                    assert(constant->m_width == 1);
                    if (constant->m_value == 1) num_one  += 1;
                    else                        num_zero += 1;
                }
            }

            // If there are no constants, skip
            if (num_zero == 0 && num_one == 0) continue;

            // Track if the gate is dropped and needs to be cleaned up
            bool dropped = false;

            // Condition expressions (A ? B : C)
            if (gate->m_op == NXGate::COND) {
                // Skip if the condition is not constant
                auto cond = gate->m_inputs[0];
                if (cond->m_type != NXSignal::CONSTANT) continue;
                // Pickup the term to propagate
                std::shared_ptr<NXSignal> to_prop;
                // If condition is non-zero, propagate the first term
                if (NXConstant::from_signal(cond)->m_value != 0)
                    to_prop = gate->m_inputs[1];
                // Otherwise, propagate the second term
                else
                    to_prop = gate->m_inputs[2];
                // Relink all of the outputs
                for (auto driven : gate->m_outputs) {
                    driven->remove_input(gate);
                    driven->add_input(to_prop);
                    to_prop->add_output(driven);
                }
                // Mark gate as dropped
                dropped = true;

            // Unary expression
            } else if (gate->m_inputs.size() == 1) {
                // Decide if this can be optimised
                bool         flatten = false;
                unsigned int value   = 0;
                switch (gate->m_op) {
                    case NXGate::AND: {
                        flatten = (num_var  == 0 || num_zero > 0);
                        value   = (num_zero == 0);
                        break;
                    }
                    case NXGate::OR: {
                        flatten = (num_var == 0 || num_one > 0);
                        value   = (num_one >  0);
                        break;
                    }
                    case NXGate::NOT: {
                        flatten = (num_one >  0);
                        value   = (num_one == 0 && num_var == 0);
                        break;
                    }
                    case NXGate::XOR: {
                        flatten = (num_var == 0);
                        value   = ((num_one % 2) == 1);
                        break;
                    }
                    default: {
                        assert(!"Unsupported gate type");
                    }
                }

                // If can't flatten, skip
                if (!flatten) continue;

                // Form a new constant and relink outputs
                auto new_const = std::make_shared<NXConstant>(value, 1);
                for (auto output : gate->m_outputs) {
                    output->remove_input(gate);
                    output->add_input(new_const);
                    new_const->add_output(output);
                }

                // Mark gate as dropped
                dropped = true;

            // Binary expression
            } else if (gate->m_inputs.size() == 2) {
                // Extract operands
                auto lhs = gate->m_inputs[0];
                auto rhs = gate->m_inputs[1];

                // If both operands are constant
                if (num_var == 0) {
                    unsigned int new_val = 0;
                    switch (gate->m_op) {
                        case NXGate::AND:
                            new_val = (num_zero == 0);
                            break;
                        case NXGate::OR:
                            new_val = (num_one > 0);
                            break;
                        case NXGate::XOR:
                            new_val = (num_one == 1);
                            break;
                        default:
                            assert(!"Unsupported gate");
                    }
                    auto new_const = std::make_shared<NXConstant>(new_val, 1);
                    for (auto output : gate->m_outputs) {
                        output->remove_input(gate);
                        output->add_input(new_const);
                        new_const->add_output(output);
                    }
                    dropped = true;

                // If LHS is constant
                } else if (lhs->m_type == NXGate::CONSTANT) {
                    auto lhs_value = NXConstant::from_signal(lhs)->m_value;
                    switch (gate->m_op) {
                        case NXGate::AND: {
                            if (lhs_value != 0) {
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(rhs);
                                    rhs->add_output(output);
                                }
                            } else {
                                auto new_const = std::make_shared<NXConstant>(0, 1);
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(new_const);
                                    new_const->add_output(output);
                                }
                            }
                            dropped = true;
                            break;
                        }
                        case NXGate::OR: {
                            if (lhs_value == 0) {
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(rhs);
                                    rhs->add_output(output);
                                }
                            } else {
                                auto new_const = std::make_shared<NXConstant>(1, 1);
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(new_const);
                                    new_const->add_output(output);
                                }
                            }
                            dropped = true;
                            break;
                        }
                        // Other gate types can't be so easily reduced
                        default:
                            break;
                    }

                // If RHS is constant
                } else if (rhs->m_type == NXGate::CONSTANT) {
                    auto rhs_value = NXConstant::from_signal(rhs)->m_value;
                    switch (gate->m_op) {
                        case NXGate::AND: {
                            if (rhs_value != 0) {
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(rhs);
                                    lhs->add_output(output);
                                }
                            } else {
                                auto new_const = std::make_shared<NXConstant>(0, 1);
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(new_const);
                                    new_const->add_output(output);
                                }
                            }
                            dropped = true;
                            break;
                        }
                        case NXGate::OR: {
                            if (rhs_value == 0) {
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(rhs);
                                    lhs->add_output(output);
                                }
                            } else {
                                auto new_const = std::make_shared<NXConstant>(1, 1);
                                for (auto output : gate->m_outputs) {
                                    output->remove_input(gate);
                                    output->add_input(new_const);
                                    new_const->add_output(output);
                                }
                            }
                            dropped = true;
                            break;
                        }
                        // Other gate types can't be so easily reduced
                        default:
                            break;
                    }

                // ???
                } else {
                    assert(!"Unexpected outcome");
                }

            // Unsupported
            } else {
                assert(!"Unsupported gate type");
            }

            // If this gate was marked as dropped, add to list to clean-up
            if (dropped) to_drop.push_back(gate);
        }

        // Search through flops, looking for constant inputs
        PLOGI << "Starting flop elimination pass " << passes;
        for (auto flop : module->m_flops) {
            // Skip flops not driven by constants
            if (flop->m_inputs[0]->m_type != NXSignal::CONSTANT) continue;
            // Propagate constant through the flop
            for (auto output : flop->m_outputs) {
                output->remove_input(flop);
                output->add_input(flop->m_inputs[0]);
                flop->m_inputs[0]->add_output(flop);
            }
            // Add it to the list of signals to drop
            to_drop.push_back(flop);
        }

        // Clean up dropped flops and gates
        PLOGI << "Optimisation pass " << passes << " dropped " << to_drop.size()
              << " flops/gates";
        for (auto entry : to_drop) {
            for (auto input : entry->m_inputs) input->remove_output(entry);
            entry->clear_inputs();
            entry->clear_outputs();
            module->drop_signal(entry);
            drop_count += 1;
        }
    } while (drop_count > 0);

    PLOGI << "Complete propagation in " << passes << " passes";
}
