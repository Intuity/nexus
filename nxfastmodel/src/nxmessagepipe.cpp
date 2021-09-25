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
#include "nxmessagepipe.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXMessagePipe::enqueue (node_load_instr_t message)
{
    entry_t entry;
    entry.header = message.header;
    pack_node_load_instr(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXMessagePipe::enqueue (node_map_output_t message)
{
    entry_t entry;
    entry.header = message.header;
    pack_node_map_output(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXMessagePipe::enqueue (node_sig_state_t message)
{
    entry_t entry;
    entry.header = message.header;
    pack_node_sig_state(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXMessagePipe::enqueue (node_raw_t message)
{
    entry_t entry;
    entry.header = message.header;
    pack_node_raw(message, (uint8_t *)&entry.encoded);
    m_messages.push(entry);
}

void NXMessagePipe::enqueue_raw (entry_t entry)
{
    m_messages.push(entry);
}

bool NXMessagePipe::is_idle (void)
{
    return m_messages.empty();
}

node_command_t NXMessagePipe::next_type (void)
{
    if (m_messages.empty()) assert(!"Called next_type on empty pipe");
    entry_t front = m_messages.front();
    return front.header.command;
}

node_header_t NXMessagePipe::next_header (void)
{
    if (m_messages.empty()) assert(!"Called next_header on empty pipe");
    entry_t front = m_messages.front();
    return front.header;
}

void NXMessagePipe::dequeue (node_load_instr_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_node_load_instr((uint8_t *)&front.encoded);
}

void NXMessagePipe::dequeue (node_map_output_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_node_map_output((uint8_t *)&front.encoded);
}

void NXMessagePipe::dequeue (node_sig_state_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_node_sig_state((uint8_t *)&front.encoded);
}

void NXMessagePipe::dequeue (node_raw_t & message)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t front = m_messages.front();
    m_messages.pop();
    message = unpack_node_raw((uint8_t *)&front.encoded);
}

NXMessagePipe::entry_t NXMessagePipe::dequeue_raw (void)
{
    if (m_messages.empty()) assert(!"Called dequeue on empty pipe");
    entry_t entry = m_messages.front();
    m_messages.pop();
    return entry;
}
