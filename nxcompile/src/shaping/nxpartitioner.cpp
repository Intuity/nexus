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
#include <set>

#include <plog/Log.h>

#include "nxpartitioner.hpp"

using namespace Nexus;

// chase_to_source
// Chase a signal backwards until reaching the first significant source
//
std::shared_ptr<NXSignal> NXPartition::chase_to_source (
    std::shared_ptr<NXSignal> ptr
) {
    return (ptr->m_type != NXSignal::WIRE) ? ptr
                                           : chase_to_source(ptr->m_inputs[0]);
}

// chase_to_targets
// Chase a signal forwards until reaching the first significant targets on each
// branch followed
//
std::vector< std::shared_ptr<NXSignal> > NXPartition::chase_to_targets (
      std::shared_ptr<NXSignal> ptr
    , bool                      thru_gates /* =false */
) {
    std::vector< std::shared_ptr<NXSignal> > vector;
    if (
        (ptr->m_type != NXSignal::WIRE               ) &&
        (!thru_gates || ptr->m_type != NXSignal::GATE)
    ) {
        vector.push_back(ptr);
    } else {
        // Always track gates (even if thru_gates is true)
        if (ptr->m_type == NXSignal::GATE) vector.push_back(ptr);
        // Search through outputs
        for (auto output : ptr->m_outputs) {
            auto recurse = NXPartition::chase_to_targets(output);
            vector.insert(vector.end(), recurse.begin(), recurse.end());
        }
    }
    return vector;
}

std::set<std::shared_ptr<NXSignal>> NXPartition::trace_inputs (
    std::shared_ptr<NXSignal> root
) {
    std::set<std::shared_ptr<NXSignal>> traced;
    for (auto input : root->m_inputs) {
        // Chase back to the first flop/gate on the path
        auto source = NXPartition::chase_to_source(input);
        // Skip over constants
        if (source->m_type == NXSignal::CONSTANT) continue;
        // Check this is a supported type
        assert(
            (source->m_type == NXSignal::GATE) ||
            (source->m_type == NXSignal::FLOP) ||
            (source->m_type == NXSignal::PORT)
        );
        // Check the partition on the signal
        if (source->get_tag_int("partition") != m_index) traced.insert(source);
    }
    return traced;
}

std::set<std::shared_ptr<NXSignal>> NXPartition::trace_outputs (
    std::shared_ptr<NXSignal> root
) {
    std::set<std::shared_ptr<NXSignal>> traced;
    for (auto output : root->m_outputs) {
        for (auto target : NXPartition::chase_to_targets(output)) {
            // Check this is a supported type
            assert(
                (target->m_type == NXSignal::GATE) ||
                (target->m_type == NXSignal::FLOP) ||
                (target->m_type == NXSignal::PORT)
            );
            // Check the partition on the signal
            if (target->get_tag_int("partition") != m_index) traced.insert(target);
        }
    }
    return traced;
}

std::map<std::shared_ptr<NXSignal>, unsigned int> NXPartition::required_inputs (void)
{
    std::map<std::shared_ptr<NXSignal>, unsigned int> external;
    // Trace all gates that take external inputs
    for (auto gate : m_gates) {
        for (auto input : trace_inputs(gate)) {
            if (!external.count(input)) external[input] = 0;
            external[input] += 1;
        }
    }
    // All flops, regardless of whether they are looped back, consume an input
    // NOTE: This is an artefact of the hardware
    for (auto flop : m_flops) {
        auto input = chase_to_source(flop->m_inputs[0]);
        if (!external.count(input)) external[input] = 0;
        external[input] += 1;
    }
    return external;
}

std::map<std::shared_ptr<NXSignal>, unsigned int> NXPartition::required_outputs (void)
{
    std::map<std::shared_ptr<NXSignal>, unsigned int> external;
    for (auto node : all_flops_and_gates()) {
        for (auto output : trace_outputs(node)) {
            if (!external.count(output)) external[output] = 0;
            external[output] += 1;
        }
    }
    return external;
}

bool NXPartition::fits ( unsigned int node_inputs, unsigned int node_outputs )
{
    return (
        (required_inputs().size()  <= node_inputs ) &&
        (required_outputs().size() <= node_outputs)
    );
}

std::list< std::shared_ptr<NXSignal> > NXPartition::all_flops_and_gates ( void )
{
    std::list< std::shared_ptr<NXSignal> > all_sigs;
    for (auto gate : m_gates) all_sigs.push_back(gate);
    for (auto flop : m_flops) all_sigs.push_back(flop);
    return all_sigs;
}

void NXPartitioner::run ( void )
{
    // Start by placing all gates and flops into a single partition
    PLOGI << "Forming initial partition";
    auto first = std::make_shared<NXPartition>(0, shared_from_this());
    for (auto gate : m_module->m_gates) first->add(gate);
    for (auto flop : m_module->m_flops) first->add(flop);
    m_partitions.push_back(first);

    // Loop until all partitions fit into the available I/O
    bool         all_fit = true;
    unsigned int part_idx = 1;
    do {
        // Reset marker to break out on a clean pass
        all_fit = true;
        // Iterate through partitions
        // NOTE: lhs/rhs do not have a physical connotation other that signifying
        //       two sides of the partition boundary
        std::list< std::shared_ptr<NXPartition> > new_partitions;
        for (auto lhs : m_partitions) {
            // Test to see if the partition fits within the budget
            if (lhs->fits(m_node_inputs, m_node_outputs)) continue;
            all_fit = false;
            PLOGI << lhs->announce();
            // Roughly bisect the existing partition, arbitrarily moving gates & flops
            auto rhs = std::make_shared<NXPartition>(part_idx, shared_from_this());
            new_partitions.push_back(rhs);
            part_idx += 1;
            while (lhs->m_flops.size() > rhs->m_flops.size()) {
                rhs->add(lhs->m_flops.front());
                lhs->m_flops.pop_front();
            }
            while (lhs->m_gates.size() > rhs->m_gates.size()) {
                rhs->add(lhs->m_gates.front());
                lhs->m_gates.pop_front();
            }

            // Log pre-optimisation state
            PLOGI << "Pre-optimisation:";
            PLOGI << " - LHS: " << lhs->announce();
            PLOGI << " - RHS: " << rhs->announce();

            // Use a KL algorithm to minimise cost of the partition
            PLOGI << "Executing KL optimisation:";
            for (unsigned int pass = 0; pass < 10; pass++) {
                // Track if a swap was made
                unsigned int swap_count = 0;

                // Take a copy of LHS & RHS arrays
                auto all_lhs = lhs->all_flops_and_gates();
                auto all_rhs = rhs->all_flops_and_gates();

                // Determine baseline I/O for LHS/RHS at this point
                auto lhs_inputs  = lhs->required_inputs();
                auto lhs_outputs = lhs->required_outputs();
                auto rhs_inputs  = rhs->required_inputs();
                auto rhs_outputs = rhs->required_outputs();

                // Sum up the I/O counts
                unsigned int lhs_base_ios = 0;
                unsigned int rhs_base_ios = 0;
                for (auto entry : lhs_inputs ) lhs_base_ios += entry.second;
                for (auto entry : lhs_outputs) lhs_base_ios += entry.second;
                for (auto entry : rhs_inputs ) rhs_base_ios += entry.second;
                for (auto entry : rhs_outputs) rhs_base_ios += entry.second;

                // Iterate through all gates/flops in the LHS
                for (auto lhs_sig : all_lhs) {
                    unsigned int lhs_trial_ios = lhs_base_ios;
                    unsigned int rhs_trial_ios = rhs_base_ios;

                    // Make adjustments to LHS I/O counts
                    auto lhs_orig_inputs  = lhs->trace_inputs(lhs_sig);
                    auto lhs_orig_outputs = lhs->trace_outputs(lhs_sig);
                    lhs_trial_ios -= lhs_orig_inputs.size() + lhs_orig_outputs.size();
                    // Move the LHS signal to the RHS
                    lhs->remove(lhs_sig);
                    rhs->add(lhs_sig);
                    // Make adjustments to the RHS I/O counts
                    auto lhs_move_inputs  = rhs->trace_inputs(lhs_sig);
                    auto lhs_move_outputs = rhs->trace_outputs(lhs_sig);
                    rhs_trial_ios += lhs_move_inputs.size() + lhs_move_outputs.size();

                    // Iterate through all gates/flops in the RHS
                    for (auto rhs_sig : all_rhs) {
                        // Skip if already marked as swapped in this pass
                        if (rhs_sig->get_tag_int("swapped", 0)) continue;

                        // Make adjustments to RHS I/O counts
                        auto rhs_orig_inputs  = rhs->trace_inputs(rhs_sig);
                        auto rhs_orig_outputs = rhs->trace_outputs(rhs_sig);
                        unsigned int rhs_cand_ios = rhs_trial_ios - rhs_orig_inputs.size() + rhs_orig_outputs.size();
                        // Move the RHS signal to the LHS
                        rhs->remove(rhs_sig);
                        lhs->add(rhs_sig);
                        // Make adjustments to the LHS I/O counts
                        auto rhs_move_inputs  = lhs->trace_inputs(rhs_sig);
                        auto rhs_move_outputs = lhs->trace_outputs(rhs_sig);
                        unsigned int lhs_cand_ios = lhs_trial_ios + rhs_move_inputs.size() + rhs_move_outputs.size();

                        // Does this move yield a net improvement?
                        if ((lhs_cand_ios + rhs_cand_ios) < (lhs_base_ios + rhs_base_ios)) {
                            // PLOGI << " - Swapping " << lhs_sig->m_name
                            //       << " with " << rhs_sig->m_name;
                            // Mark that a swap happened
                            swap_count += 1;
                            // Update base I/O counts with these new values
                            lhs_base_ios = lhs_cand_ios;
                            rhs_base_ios = rhs_cand_ios;
                            // Mark signals as swapped
                            lhs_sig->set_tag("swapped", 1);
                            rhs_sig->set_tag("swapped", 1);
                            break;
                        // Otherwise, move signal back to RHS
                        } else {
                            lhs->remove(rhs_sig);
                            rhs->add(rhs_sig);
                        }
                    }
                    // If LHS signal not marked for swap, move it back
                    if (!lhs_sig->get_tag_int("swapped", 0)) {
                        rhs->remove(lhs_sig);
                        lhs->add(lhs_sig);
                    }
                }

                // Stop searching if no swaps were made in this pass
                PLOGI << "KL pass " << std::dec << pass << " made "
                      << swap_count << " swaps:";
                PLOGI << " - LHS: " << lhs->announce();
                PLOGI << " - RHS: " << rhs->announce();
                if (swap_count == 0) break;

                // Reset all swap markers
                for (auto lhs_sig : all_lhs) lhs_sig->set_tag("swapped", 0);
                for (auto rhs_sig : all_rhs) rhs_sig->set_tag("swapped", 0);
            }

            // Report on the partitions formed
            PLOGI << "Step summary:";
            PLOGI << " - LHS: " << lhs->announce();
            PLOGI << " - RHS: " << rhs->announce();
        }

        // Merge all new partitions into the main list
        m_partitions.insert(m_partitions.end(), new_partitions.begin(), new_partitions.end());
    } while (!all_fit);
    PLOGI << "Partitioning summary:";
    for (auto part : m_partitions) {
        PLOGI << " - " << part->announce() << ": "
              << (part->fits(m_node_inputs, m_node_outputs) ? "FITS" : "DOESN'T FIT");
    }
}
