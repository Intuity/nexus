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
#include <chrono>
#include <sstream>

#include <plog/Log.h>

#include "vcd_writer.h"

#include "nexus.hpp"

using namespace NXModel;

Nexus::Nexus (
    uint32_t rows,
    uint32_t columns
)   : m_rows    ( rows          )
    , m_columns ( columns       )
{
    // Link the ingress & egress pipes
    m_control = std::make_shared<NXControl>(m_rows, m_columns);
    m_mesh    = std::make_shared<NXMesh>(m_rows, m_columns);
    m_ingress = m_mesh->get_node(0, 0)->get_pipe(DIRECTION_NORTH);
    m_egress  = std::make_shared<NXMessagePipe>();
    m_mesh->get_aggregator(0)->attach(m_egress);
    m_control->attach_to_mesh(m_ingress);
    m_control->attach_from_mesh(m_egress);
}

void Nexus::reset (void)
{
    m_control->reset();
    m_mesh->reset();
    if (m_ingress != NULL) m_ingress->reset();
    if (m_egress  != NULL) m_egress->reset();
}

void Nexus::run (uint32_t cycles, bool with_trigger /* = true */)
{
    PLOGI << "[Nexus] Running for " << cycles << " cycles";
    // Take timestamp at start of run
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    // Run for the requested number of cycles
    uint8_t outputs[NXAggregator::SLOTS * m_columns];
    for (uint32_t cycle = 0; cycle < cycles; cycle++) {
        PLOGD << "[Nexus] Starting cycle " << cycle;
        // Step until mesh and controller become idle
        uint32_t steps = 0;
        do  {
            m_control->step();
            m_mesh->step(with_trigger && (steps == 0));
            steps++;
        } while (!m_mesh->is_idle() || !m_control->is_idle());
        PLOGD << "[Nexus] Finished cycle " << cycle << " in " << steps << " steps";
        // Update the controller's output state
        m_mesh->get_outputs(outputs);
        m_control->update_outputs(outputs);
    }
    // Work out delta
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    uint64_t delta_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - begin).count();
    uint64_t rate     = delta_ns / ((uint64_t)cycles);
    uint64_t freq     = (1E9 / rate);
    PLOGI << "[Nexus] Achieved frequency of " << freq << " Hz";
}

void Nexus::dump_vcd (const std::string path)
{
    PLOGI << "[Nexus] Writing VCD to " << path;
    vcd::VCDWriter writer(path);
    // Create a cycle count signal
    vcd::VarPtr cycle = writer.register_var("dut", "cycle", vcd::VariableType::integer, 32);
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
            "dut", ss.str().c_str(), vcd::VariableType::reg, 8
        );
    }
    // Set an initial value for all signals
    writer.change(cycle, 1, std::bitset<32>(0).to_string());
    for (
        std::map<output_key_t, vcd::VarPtr>::iterator it = output_vars.begin();
        it != output_vars.end(); it++
    ) writer.change((vcd::VarPtr)it->second, 1, std::bitset<8>(0).to_string());
    // Run through every timestamp
    int step = 2;
    PLOGI << "[Nexus] Recording " << std::dec << m_output.size() << " steps";
    while (m_output.size()) {
        writer.change(cycle, step, std::bitset<32>(step).to_string());
        summary_t * summary = m_output.front();
        for (
            typename summary_t::iterator it = summary->begin();
            it != summary->end(); it++
        ) {
            output_key_t key   = it->first;
            uint8_t      state = it->second;
            writer.change(output_vars[key], step, std::bitset<8>(state).to_string());
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
