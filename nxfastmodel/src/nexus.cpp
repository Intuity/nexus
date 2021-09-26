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
#include <chrono>
#include <sstream>

#include "vcd_writer.h"

#include "nexus.hpp"

using namespace NXModel;

Nexus::Nexus (uint32_t rows, uint32_t columns)
    : m_rows    ( rows          )
    , m_columns ( columns       )
{
    // Link the ingress & egress pipes
    m_mesh    = std::make_shared<NXMesh>(m_rows, m_columns);
    m_ingress = m_mesh->get_node(0, 0)->get_pipe(DIRECTION_NORTH);
    m_egress  = std::make_shared<NXMessagePipe>();
    m_mesh->get_node(m_rows-1, 0)->attach(DIRECTION_SOUTH, m_egress);
}

void Nexus::run (uint32_t cycles)
{
    std::cout << "[NXMesh] Running for " << cycles << " cycles" << std::endl;
    // Take timestamp at start of run
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    // Run for the requested number of cycles
    for (uint32_t cycle = 0; cycle < cycles; cycle++) {
        // std::cout << "[NXMesh] Starting cycle " << cycle << std::endl;
        // Step until idle
        uint32_t steps = 0;
        do  {
            m_mesh->step((steps == 0));
            steps++;
        } while (!m_mesh->is_idle());
        // std::cout << "[NXMesh] Finished cycle " << cycle << " in "
        //           << steps << " steps" << std::endl;
        // Summarise final output state
        summary_t * summary = new summary_t();
        // - Base the summary on the previous cycle
        if (m_output.size() > 0) {
            summary_t * last = m_output.back();
            for (typename summary_t::iterator it = last->begin(); it != last->end(); it++) {
                output_key_t key   = it->first;
                bool         state = it->second;
                (*summary)[key] = state;
            }
        }
        // - Digest all queued egress messages
        while (!m_egress->is_idle()) {
            node_header_t header = m_egress->next_header();
            // Skip everything but signal state messages
            if (header.command != NODE_COMMAND_SIG_STATE) {
                m_egress->dequeue_raw();
                continue;
            }
            // Summarise final signal state
            node_sig_state_t msg;
            m_egress->dequeue(msg);
            output_key_t key = { msg.header.row, msg.header.column, msg.index };
            (*summary)[key] = msg.state;
        }
        // - Summarise the output
        // std::cout << "[NXMesh] Cycle " << cycle << " state: " << std::endl;
        // for (typename summary_t::iterator it = summary->begin(); it != summary->end(); it++) {
        //     output_key_t key   = it->first;
        //     bool         state = it->second;
        //     std::cout << " - "
        //               << std::get<0>(key) << ", "
        //               << std::get<1>(key) << ", "
        //               << std::get<2>(key) << " = "
        //               << state << std::endl;
        // }
        // Record state
        m_output.push_back(summary);
    }
    // Work out delta
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    uint64_t delta_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - begin).count();
    uint64_t rate     = delta_ns / ((uint64_t)cycles);
    uint64_t freq     = (1E9 / rate);
    std::cout << "[Nexus] Achieved frequency of " << freq << " Hz" << std::endl;
}

void Nexus::dump_vcd (const std::string path)
{
    std::cout << "[Nexus] Writing VCD to " << path << std::endl;
    // vcd::HeadPtr head = vcd::makeVCDHeader(
    //     vcd::TimeScale::ONE, vcd::TimeScaleUnit::ns, vcd::utils::now()
    // );
    vcd::VCDWriter writer(path); // , head);
    // Register all outputs
    std::map<output_key_t, vcd::VarPtr> output_vars;
    for (
        typename summary_t::iterator it = m_output.back()->begin();
        it != m_output.back()->end(); it++
    ) {
        output_key_t key = it->first;
        std::stringstream ss;
        ss << "R" << (int)std::get<0>(key) << "C" << (int)std::get<1>(key)
            << "I" << (int)std::get<2>(key);
        output_vars[key] = writer.register_var(
            "dut", ss.str().c_str(), vcd::VariableType::integer, 1
        );
    }
    // Set an initial value for all signals
    for (
        std::map<output_key_t, vcd::VarPtr>::iterator it = output_vars.begin();
        it != output_vars.end(); it++
    ) writer.change((vcd::VarPtr)it->second, 0, "0");
    // Run through every timestamp
    int step = 1;
    while (m_output.size()) {
        summary_t * summary = m_output.front();
        for (
            typename summary_t::iterator it = summary->begin();
            it != summary->end(); it++
        ) {
            output_key_t key   = it->first;
            bool         state = it->second;
            writer.change(
                output_vars[key], step,
                vcd::utils::format(state ? "1" : "0")
            );
        }
        step += 1;
        m_output.pop_front();
        delete summary;
    }
}

Nexus::summary_t * Nexus::pop_output (void)
{
    assert(m_output.size() > 0);
    summary_t * output = m_output.front();
    m_output.pop_front();
    return output;
}
