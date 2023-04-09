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
#include <bitset>
#include <iomanip>
#include <sstream>

#include <plog/Log.h>

#include "nxaggregator.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXAggregator::set_node_id (node_id_t node_id)
{
    m_id = node_id;
}

void NXAggregator::set_node_id (uint8_t row, uint8_t column)
{
    m_id.row    = row;
    m_id.column = column;
}

void NXAggregator::reset (void)
{
    m_inbound_mesh->reset();
    m_inbound_neighbour->reset();
    for (int idx = 0; idx < SLOTS; idx++) m_outputs[idx] = 0;
}

bool NXAggregator::is_idle (void)
{
    return m_inbound_mesh->is_idle() && m_inbound_neighbour->is_idle();
}

void NXAggregator::step (void)
{
    // Digest messages arriving from the mesh
    while (!m_inbound_mesh->is_idle()) {
        node_header_t header = m_inbound_mesh->next_header();
        if (header.target.column == m_id.column &&
            header.command == NODE_COMMAND_SIGNAL) {
            node_output_t output;
            m_inbound_mesh->dequeue(output);
            // If the bypass flag is set, send on to the host
            if (output.bypass) {
                uint64_t packed;
                pack_node_output(output, (uint8_t *)&packed);
                node_signal_t signal = unpack_node_signal((uint8_t *)&packed);
                m_outbound->enqueue(signal);
            // Otherwise, update the output
            } else {
                m_outputs[output.slot] = (output.data            &  output.mask) |
                                         (m_outputs[output.slot] & ~output.mask);
            }
        } else {
            m_outbound->enqueue_raw(m_inbound_mesh->dequeue_raw());
        }
    }

    // Forward messages arriving from the neighbour
    while (!m_inbound_neighbour->is_idle()) {
        m_outbound->enqueue_raw(m_inbound_neighbour->dequeue_raw());
    }
}
