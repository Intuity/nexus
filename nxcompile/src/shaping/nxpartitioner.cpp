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
            auto recurse = chase_to_targets(output);
            vector.insert(vector.end(), recurse.begin(), recurse.end());
        }
    }
    return vector;
}

unsigned int NXPartition::required_inputs (void)
{
    unsigned int total = 0;
    // All flops must be inputs due to hardware architecture
    total += m_flops.size();
    // Search all gates for inputs coming from other partitions
    std::set<std::shared_ptr<NXSignal>> external;
    for (auto gate : m_gates) {
        for (auto input : gate->m_inputs) {
            // Chase back to the first significant signal
            auto sig = chase_to_source(input);
            // Skip constants
            if (sig->m_type == NXSignal::CONSTANT) continue;
            // Check this is a supported type
            assert(
                (sig->m_type == NXSignal::GATE) ||
                (sig->m_type == NXSignal::FLOP) ||
                (sig->m_type == NXSignal::PORT)
            );
            // Check the partition on the input
            if (sig->get_tag_int("partition") != m_index) {
                external.insert(sig);
            }
        }
    }
    total += external.size();
    // Return the total number of inputs
    return total;
}

unsigned int NXPartition::required_outputs (void)
{
    // Search all gates for outputs going to other partitions
    std::set<std::shared_ptr<NXSignal>> external;
    for (auto gate : m_gates) {
        for (auto output : gate->m_outputs) {
            for (auto sig : chase_to_targets(output)) {
                // Check this is a supported type
                assert(
                    (sig->m_type == NXSignal::GATE) ||
                    (sig->m_type == NXSignal::FLOP) ||
                    (sig->m_type == NXSignal::PORT)
                );
                // Check the partition on the output
                if (sig->get_tag_int("partition") != m_index) {
                    external.insert(sig);
                }
            }
        }
    }
    // Search all flops for outputs driving ports
    for (auto flop : m_flops) {
        for (auto output : flop->m_outputs) {
            for (auto sig : chase_to_targets(output)) {
                // Skip anything except ports
                if (sig->m_type != NXSignal::PORT) continue;
                // Always append ports to external
                external.insert(sig);
            }
        }
    }
    // Return the total number of outputs
    return external.size();
}

bool NXPartition::fits ( unsigned int node_inputs, unsigned int node_outputs )
{
    unsigned int req_ins  = required_inputs();
    unsigned int req_outs = required_outputs();
    PLOGI << "Partition " << std::dec << m_index << " needs "
          << req_ins << " inputs and "
          << req_outs << " outputs, and is allowed "
          << node_inputs << " inputs and "
          << node_outputs << " outputs";
    return (
        (required_inputs()  <= node_inputs ) &&
        (required_outputs() <= node_outputs)
    );
}

void NXPartitioner::run ( void )
{
    // Start by placing all gates and flops into a single partition
    PLOGI << "Forming initial partition";
    auto first = std::make_shared<NXPartition>(0, shared_from_this());
    for (auto gate : m_module->m_gates) first->add(gate);
    for (auto flop : m_module->m_flops) first->add(flop);
    m_partitions.push_back(first);
    PLOGI << first->announce();

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
            // Form a new partition
            auto rhs = std::make_shared<NXPartition>(part_idx, shared_from_this());
            new_partitions.push_back(rhs);
            part_idx += 1;
            // Move half the flops into the new partition
            while (lhs->m_flops.size() > rhs->m_flops.size()) {
                rhs->add(lhs->m_flops.front());
                lhs->m_flops.pop_front();
            }
            // Move fan-out logic from the flops into the new partition
            for (auto flop : rhs->m_flops) {
                for (auto output : flop->m_outputs) {
                    for (auto target : lhs->chase_to_targets(output, true)) {
                        // Skip outputs which aren't gates
                        if (target->m_type != NXSignal::GATE) continue;
                        // Skip gates which aren't associated to the LHS partition
                        if (target->get_tag_int("partition") != lhs->m_index) continue;
                        // Move the gate
                        auto gate = NXGate::from_signal(target);
                        rhs->add(gate);
                        lhs->m_gates.remove(gate);
                    }
                }
            }
            // Report on the partitions formed
            PLOGI << "LHS: " << lhs->announce();
            PLOGI << "RHS: " << rhs->announce();
        }

        // Merge all new partitions into the main list
        m_partitions.insert(m_partitions.end(), new_partitions.begin(), new_partitions.end());

        // TODO: Temporary break
        if (part_idx > 10) break;
    } while (!all_fit);
}
