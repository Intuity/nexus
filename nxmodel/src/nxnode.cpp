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

#include "nxnode.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXNode::attach (direction_t dirx, std::shared_ptr<NXMessagePipe> pipe)
{
    assert(dirx >= 0 && ((uint32_t)dirx) < 4);
    assert(m_outbound[(int)dirx] == NULL);
    m_outbound[(int)dirx] = pipe;
}

std::shared_ptr<NXMessagePipe> NXNode::get_pipe (direction_t dirx)
{
    assert(dirx >= 0 && ((uint32_t)dirx) < 4);
    return m_inbound[(int)dirx];
}

void NXNode::reset (void)
{
    m_seen_first = false;
    m_accumulator = 0;
    m_memory.clear();
    m_num_instr  = 0;
    m_num_output = 0;
    m_loopback   = 0;
    m_inputs_curr.clear();
    m_inputs_next.clear();
    m_outputs.clear();
}

bool NXNode::is_idle (void)
{
    return (
        (m_inbound[0] == NULL || m_inbound[0]->is_idle()) &&
        (m_inbound[1] == NULL || m_inbound[1]->is_idle()) &&
        (m_inbound[2] == NULL || m_inbound[2]->is_idle()) &&
        (m_inbound[3] == NULL || m_inbound[3]->is_idle())
    );
}

void NXNode::step (bool trigger)
{
    // On the first triggered cycle, always evaluate instructions
    bool ip_delta = (!m_seen_first && trigger);

    // If a trigger is received, copy next->current
    if (trigger) {
        for (io_state_t::iterator it = m_inputs_next.begin(); it != m_inputs_next.end(); it++) {
            uint32_t index = it->first;
            bool     state = it->second;
            // Is this a change in value
            ip_delta |= (state != get_input(index));
            // Update the value
            m_inputs_curr[index] = state;
        }
    }

    // Digest inbound messages
    ip_delta |= digest();

    // Perform execution
    bool op_delta = false;
    if (ip_delta) op_delta = evaluate();

    // Generate outbound messages
    if (op_delta) transmit();

    // Record whether a trigger has ever been seen
    m_seen_first |= trigger;
}

std::vector<uint32_t> NXNode::get_memory (void)
{
    return m_memory;
}

NXNode::io_state_t NXNode::get_current_inputs (void)
{
    return m_inputs_curr;
}

NXNode::io_state_t NXNode::get_next_inputs (void)
{
    return m_inputs_next;
}

NXNode::io_state_t NXNode::get_current_outputs (void)
{
    return m_outputs;
}

bool NXNode::digest (void)
{
    bool curr_delta = false;
    for (int idx_pipe = 0; idx_pipe < 4; idx_pipe++)
    {
        std::shared_ptr<NXMessagePipe> pipe = m_inbound[idx_pipe];
        // Skip unconnected pipes
        if (pipe == NULL) continue;
        // Iterate until pipe is empty
        while (!pipe->is_idle()) {
            node_header_t   header = pipe->next_header();
            // Is the message targeted at this node?
            if (header.row == m_row && header.column == m_column) {
                // std::cout << "[NXNode " << m_row << ", " << m_column << "] "
                //           << "Received command " << header.command << std::endl;
                switch (header.command) {
                    case NODE_COMMAND_LOAD: {
                        node_load_t msg;
                        pipe->dequeue(msg);
                        // Accumulate the value
                        m_accumulator = (
                            (m_accumulator << LOAD_SEG_WIDTH) |
                            msg.data
                        );
                        // When the last flag is set, load into the memory
                        if (msg.last) {
                            m_memory.push_back(m_accumulator);
                            m_accumulator = 0;
                        }
                        break;
                    }
                    case NODE_COMMAND_LOOPBACK: {
                        node_loopback_t msg;
                        pipe->dequeue(msg);
                        // Create a mask for this section
                        uint64_t shift = msg.section * LB_SECTION_WIDTH;
                        uint64_t mask  = ((1 << LB_SECTION_WIDTH) - 1) << shift;
                        // Update the held loopback
                        m_loopback = (
                            (m_loopback & ~mask) |
                            ((msg.section << shift) & mask)
                        );
                        break;
                    }
                    case NODE_COMMAND_SIGNAL: {
                        node_signal_t msg;
                        pipe->dequeue(msg);
                        // Update input state
                        m_inputs_next[msg.index] = msg.state;
                        if (!msg.is_seq) {
                            curr_delta = (m_inputs_curr[msg.index] != msg.state);
                            m_inputs_curr[msg.index] = msg.state;
                        }
                        break;
                    }
                    case NODE_COMMAND_CONTROL: {
                        node_control_t msg;
                        pipe->dequeue(msg);
                        switch (msg.param) {
                            case NODE_PARAMETER_INSTRUCTIONS:
                                m_num_instr = msg.value;
                                break;
                            case NODE_PARAMETER_OUTPUTS:
                                m_num_output = msg.value;
                                break;
                            default:
                                assert(!"Unsupported control parameter");
                                break;
                        }
                        break;
                    }
                    default: assert(!"Unsupported command received");
                }

            // Otherwise, route it towards the correct node
            } else {
                route(header.row, header.column)->enqueue_raw(
                    m_inbound[idx_pipe]->dequeue_raw()
                );
            }
        }
    }

    // Return whether the current input values have been modified
    return curr_delta;
}

bool NXNode::evaluate (void)
{
    // Declare storage for the working registers
    io_state_t working;
    auto get_reg = [&] (uint32_t index) -> bool {
        return working.count(index) ? working[index] : false;
    };
    // Iterate through instructions performing input->output transform
    uint32_t op_index = 0;
    bool     op_delta = false;
    for (uint32_t pc = 0; pc < m_num_instr; pc++) {
        uint32_t      raw_data = m_memory[pc];
        instruction_t instr    = unpack_instruction((uint8_t *)&raw_data);
        // std::cout << "[NXNode " << m_row << ", " << m_column << "] Executing -"
        //             << " TT: 0x"   << std::hex << instr.truth << std::dec
        //             << " SRC_A: "  << (instr.src_a_ip ? "I[" : "R[") << (int)instr.src_a << "]"
        //             << " SRC_B: "  << (instr.src_b_ip ? "I[" : "R[") << (int)instr.src_b << "]"
        //             << " SRC_C: "  << (instr.src_c_ip ? "I[" : "R[") << (int)instr.src_c << "]"
        //             << " TGT: "    << (int)instr.tgt_reg
        //             << " OUTPUT: " << (instr.gen_out ? "YES" : "NO")
        //             << std::endl;
        // Pickup the inputs
        bool input_a = instr.src_a_ip ? get_input(instr.src_a) : get_reg(instr.src_a);
        bool input_b = instr.src_b_ip ? get_input(instr.src_b) : get_reg(instr.src_b);
        bool input_c = instr.src_c_ip ? get_input(instr.src_c) : get_reg(instr.src_c);
        // Work out the shift
        uint32_t shift = (input_a ? 4 : 0) + (input_b ? 2 : 0) + (input_c ? 1 : 0);
        // Select the right entry from the truth table
        bool result = (((instr.truth >> shift) & 0x1) != 0);
        // Store to the target register
        working[instr.tgt_reg] = result;
        // Does this instruction generate an output?
        if (instr.gen_out) {
            // Has the output value changed
            op_delta |= (result != get_output(op_index));
            // Store the output value
            m_outputs[op_index] = result;
            // Always increment the output
            op_index++;
        }
    }
    // Return whether the outputs have updated
    return op_delta;
}

void NXNode::transmit (void)
{
    for (io_state_t::iterator it = m_outputs.begin(); it != m_outputs.end(); it++) {
        uint32_t index = it->first;
        bool     state = it->second;
        bool     last  = m_outputs_last.count(index) ? m_outputs_last[index] : false;
        // Skip outputs that are not enabled
        if (index >= m_num_output) continue;
        // Lookup the output mappings
        uint32_t raw_lookup    = m_memory[m_num_instr + index];
        output_lookup_t lookup = unpack_output_lookup((uint8_t *)&raw_lookup);
        // Fetch and generate each of the messages
        for (uint32_t addr = lookup.start; addr <= lookup.final; addr++) {
            // Sanity check
            assert(addr < MAX_NODE_MEMORY);
            // Fetch the mapping
            uint32_t         raw_mapping = m_memory[addr];
            output_mapping_t mapping     = unpack_output_mapping((uint8_t *)&raw_mapping);
            // Generate and send a message
            node_signal_t msg;
            msg.header.row     = mapping.row;
            msg.header.column  = mapping.column;
            msg.header.command = NODE_COMMAND_SIGNAL;
            msg.index          = mapping.index;
            msg.is_seq         = mapping.is_seq;
            msg.state          = state;
            // Dispatch the message
            route(mapping.row, mapping.column)->enqueue(msg);
        }
        // Always update the last sent state
        m_outputs_last[index] = state;
    }
}

bool NXNode::get_input (uint32_t index)
{
    return m_inputs_curr.count(index) ? m_inputs_curr[index] : false;
}

bool NXNode::get_output (uint32_t index)
{
    return m_outputs.count(index) ? m_outputs[index] : false;
}

std::shared_ptr<NXMessagePipe> NXNode::route (uint32_t row, uint32_t column)
{
    // NOTE: Messages routed towards unconnected pipes will be directed to
    //       adjacent pipes in a clockwise order
    assert(!(row == m_row && column == m_column));
    std::shared_ptr<NXMessagePipe> tgt_pipe = NULL;
    uint32_t start;
    if      (row    < m_row   ) start = (int)DIRECTION_NORTH;
    else if (row    > m_row   ) start = (int)DIRECTION_SOUTH;
    else if (column < m_column) start = (int)DIRECTION_WEST;
    else                        start = (int)DIRECTION_EAST;
    for (int idx_off = 0; idx_off < 4; idx_off++) {
        uint32_t trial = (start + idx_off) % 4;
        if (m_outbound[trial] == NULL) continue;
        tgt_pipe = m_outbound[trial];
        break;
    }
    assert(tgt_pipe != NULL);
    return tgt_pipe;
}
