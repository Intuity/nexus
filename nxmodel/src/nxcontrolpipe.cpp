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
#include "nxcontrolpipe.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXControlPipe::reset (void)
{
    std::queue<entry_t> empty;
    std::swap(m_messages, empty);
}

void NXControlPipe::enqueue (control_request_raw_t message)
{
    entry_t entry;
    entry.is_request = true;
    entry.req_type = message.command;
    pack_control_request_raw(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_request_configure_t message)
{
    entry_t entry;
    entry.is_request = true;
    entry.req_type = message.command;
    pack_control_request_configure(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_request_trigger_t message)
{
    entry_t entry;
    entry.is_request = true;
    entry.req_type = message.command;
    pack_control_request_trigger(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_request_to_mesh_t message)
{
    entry_t entry;
    entry.is_request = true;
    entry.req_type = message.command;
    pack_control_request_to_mesh(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_request_memory_t message)
{
    entry_t entry;
    entry.is_request = true;
    entry.req_type = message.command;
    pack_control_request_memory(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_raw_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_raw(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_parameters_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_parameters(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_status_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_status(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_outputs_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_outputs(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_from_mesh_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_from_mesh(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue (control_response_padding_t message)
{
    entry_t entry;
    entry.is_request = false;
    entry.resp_type = message.format;
    pack_control_response_padding(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXControlPipe::enqueue_raw (entry_t entry)
{
    m_messages.push(entry);
}

bool NXControlPipe::next_is_request (void)
{
    if (m_messages.empty()) assert(!"Called next_type on empty pipe");
    entry_t front = m_messages.front();
    return front.is_request;
}

control_req_type_t NXControlPipe::next_request_type (void)
{
    if (m_messages.empty()) assert(!"Called next_type on empty pipe");
    entry_t front = m_messages.front();
    return front.req_type;
}

control_resp_type_t NXControlPipe::next_response_type (void)
{
    if (m_messages.empty()) assert(!"Called next_type on empty pipe");
    entry_t front = m_messages.front();
    return front.resp_type;
}

bool NXControlPipe::is_idle (void)
{
    return m_messages.empty();
}

void NXControlPipe::dequeue (control_request_raw_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_request_raw((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_request_configure_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_request_configure((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_request_trigger_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_request_trigger((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_request_to_mesh_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_request_to_mesh((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_request_memory_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_request_memory((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_raw_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_raw((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_parameters_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_parameters((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_status_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_status((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_outputs_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_outputs((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_from_mesh_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_from_mesh((uint8_t *)&front.encoded);
}

void NXControlPipe::dequeue (control_response_padding_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_control_response_padding((uint8_t *)&front.encoded);
}

NXControlPipe::entry_t NXControlPipe::dequeue_raw (void)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    return front;
}
