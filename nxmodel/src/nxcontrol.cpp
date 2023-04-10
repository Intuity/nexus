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

#include "nxcontrol.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXControl::reset (void)
{
    memset((void *)m_last_output, 0, (size_t)m_columns);
    m_to_host->reset();
    m_from_host->reset();
    if (m_to_mesh   != nullptr) m_to_mesh->reset();
    if (m_from_mesh != nullptr) m_from_mesh->reset();
}

bool NXControl::is_idle (void)
{
    // Host pipes are excluded here as they are not involved in the execution loop
    return m_to_mesh->is_idle() && m_from_mesh->is_idle();
}

void NXControl::step (void)
{
    // Digest all messages from the host
    while (!m_from_host->is_idle()) {
        assert(m_from_host->next_is_request());
        switch (m_from_host->next_request_type()) {
            case CONTROL_REQ_TYPE_READ_PARAMS: {
                m_from_host->dequeue_raw();
                control_response_parameters_t response;
                response.format      = CONTROL_RESP_TYPE_PARAMS;
                response.id          = HW_DEV_ID;
                response.ver_major   = HW_VER_MAJOR;
                response.ver_minor   = HW_VER_MINOR;
                response.timer_width = 0; // TODO
                response.rows        = m_rows;
                response.columns     = m_columns;
                response.node_regs   = 0; // TODO
                m_to_host->enqueue(response);
                break;
            }
            case CONTROL_REQ_TYPE_READ_STATUS: {
                m_from_host->dequeue_raw();
                control_response_status_t response;
                response.format     = CONTROL_RESP_TYPE_STATUS;
                response.active     = 0; // TODO
                response.mesh_idle  = 0; // TODO
                response.agg_idle   = 0; // TODO
                response.seen_low   = 0; // TODO
                response.first_tick = 0; // TODO
                response.cycle      = 0; // TODO
                response.countdown  = 0; // TODO
                m_to_host->enqueue(response);
                break;
            }
            case CONTROL_REQ_TYPE_SOFT_RESET: {
                assert(!"Not yet implemented - SOFT_RESET");
                break;
            }
            case CONTROL_REQ_TYPE_CONFIGURE: {
                assert(!"Not yet implemented - CONFIGURE");
                break;
            }
            case CONTROL_REQ_TYPE_TRIGGER: {
                assert(!"Not yet implemented - TRIGGER");
                break;
            }
            case CONTROL_REQ_TYPE_TO_MESH: {
                // Pickup request from pipe
                control_request_to_mesh_t request;
                m_from_host->dequeue(request);
                // Push into the mesh
                node_raw_t message = unpack_node_raw((uint8_t *)&request.message);
                m_to_mesh->enqueue(message);
                break;
            }
            case CONTROL_REQ_TYPE_MEMORY: {
                assert(!"Memory accesses not yet implemented");
                break;
            }
            default: {
                assert(!"Unsupported host control request");
            }
        }
    }

    // Forward all messages from the mesh to the host
    while (!m_from_mesh->is_idle()) {
        switch (m_from_mesh->next_type()) {
            case NODE_COMMAND_LOAD:
            case NODE_COMMAND_SIGNAL: {
                // Pickup message from pipe
                node_raw_t message;
                m_from_mesh->dequeue(message);
                // Push towards the host
                control_response_from_mesh_t response;
                response.format  = CONTROL_RESP_TYPE_OUTPUTS;
                response.message = 0;
                pack_node_raw(message, (uint8_t *)&response.message);
                break;
            }
            default: {
                assert(!"Unsupported message from mesh");
            }
        }
    }
}

void NXControl::update_outputs (uint8_t * outputs)
{
    // Detect if any part of the output state updated
    bool updated = false;
    for (unsigned int column = 0; column < m_columns; column++) {
        for (unsigned int slot = 0; slot < NXAggregator::SLOTS; slot++) {
            unsigned int index = (column * NXAggregator::SLOTS) + slot;
            updated |= (m_last_output[index] != outputs[index]);
            if (updated) break;
        }
        if (updated) break;
    }

    // If a update did occur...
    if (updated) {
        // Send messages to host
        unsigned int total        = m_columns * NXAggregator::SLOTS;
        unsigned int num_msg      = (total + NXAggregator::SLOTS - 1) / NXAggregator::SLOTS;
        unsigned int slot_per_msg = 96 / NXAggregator::SLOT_W;
        for (unsigned int i_msg = 0; i_msg < num_msg; i_msg++) {
            unsigned int offset = i_msg * slot_per_msg;
            control_response_outputs_t message;
            message.format  = CONTROL_RESP_TYPE_OUTPUTS;
            message.stamp   = 0;
            message.index   = i_msg;
            message.section = 0;
            memcpy((void *)&message.section,
                   (void *)&outputs[offset],
                   std::min(slot_per_msg, total - offset));
            m_to_host->enqueue(message);
        }
        // Update the held state
        memcpy((void *)m_last_output, (void *)outputs, total);
    }
}
