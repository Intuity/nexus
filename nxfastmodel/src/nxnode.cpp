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

void NXNode::attach (direction_t dirx, NXMessagePipe * pipe)
{
    assert(dirx >= 0 && ((uint32_t)dirx) < 4);
    assert(m_outbound[(int)dirx] == NULL);
    m_outbound[(int)dirx] = pipe;
}

NXMessagePipe * NXNode::get_pipe (direction_t dirx)
{
    assert(dirx >= 0 && ((uint32_t)dirx) < 4);
    return m_inbound[(int)dirx];
}

void NXNode::reset (void)
{
    m_seen_first = false;
    m_instructions.clear();
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

void NXNode::append (NXConstants::instruction_t instr)
{
    m_instructions.push_back(instr);
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

bool NXNode::digest (void)
{
    bool curr_delta = false;
    for (int idx_pipe = 0; idx_pipe < 4; idx_pipe++)
    {
        // Skip unconnected pipes
        if (m_inbound[idx_pipe] == NULL) continue;
        // Iterate until pipe is empty
        while (!m_inbound[idx_pipe]->is_idle()) {
            node_header_t header = m_inbound[idx_pipe]->next_header();
            // Is the message targeted at this node?
            if (header.row == m_row && header.column == m_column) {
                // std::cout << "[NXNode " << m_row << ", " << m_column << "] "
                //           << "Received command " << header.command << std::endl;
                switch (header.command) {
                    case NODE_COMMAND_LOAD_INSTR: {
                        node_load_instr_t instr;
                        m_inbound[idx_pipe]->dequeue(instr);
                        append(instr.instr);
                        break;
                    }
                    case NODE_COMMAND_MAP_OUTPUT: {
                        node_map_output_t mapping;
                        m_inbound[idx_pipe]->dequeue(mapping);
                        m_mappings[mapping.source_index].push_back(mapping);
                        break;
                    }
                    case NODE_COMMAND_SIG_STATE: {
                        node_sig_state_t state;
                        m_inbound[idx_pipe]->dequeue(state);
                        m_inputs_next[state.index] = state.state;
                        if (!state.is_seq) {
                            curr_delta = (m_inputs_curr[state.index] != state.state);
                            m_inputs_curr[state.index] = state.state;
                        }
                        break;
                    }
                    case NODE_COMMAND_NODE_CTRL: {
                        assert(!"Received unexpected node control command");
                        break;
                    }
                    default: assert(!"Unsupported command received");
                }

            // Otherwise, route it towards the correct node
            } else {
                NXMessagePipe * tgt_pipe = route(header.row, header.column);
                tgt_pipe->enqueue_raw(m_inbound[idx_pipe]->dequeue_raw());
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
    for (const instruction_t & instr : m_instructions) {
        // std::cout << "[NXNode " << m_row << ", " << m_column << "] Executing -"
        //             << " OPCODE: " << (int)instr.opcode
        //             << " SRC_A: "  << (instr.src_a_ip ? "I[" : "R[") << (int)instr.src_a << "]"
        //             << " SRC_B: "  << (instr.src_b_ip ? "I[" : "R[") << (int)instr.src_b << "]"
        //             << " TGT: "    << (int)instr.tgt_reg
        //             << " OUTPUT: " << (instr.gen_out ? "YES" : "NO")
        //             << std::endl;
        // Pickup the inputs
        bool input_a = instr.src_a_ip ? get_input(instr.src_a) : get_reg(instr.src_a);
        bool input_b = instr.src_b_ip ? get_input(instr.src_b) : get_reg(instr.src_b);
        // Perform the operation
        bool result = false;
        switch (instr.opcode) {
            case OPERATION_INVERT : { result = !(input_a           ); break; }
            case OPERATION_AND    : { result =  (input_a && input_b); break; }
            case OPERATION_NAND   : { result = !(input_a && input_b); break; }
            case OPERATION_OR     : { result =  (input_a || input_b); break; }
            case OPERATION_NOR    : { result = !(input_a || input_b); break; }
            case OPERATION_XOR    : { result =  (input_a ^  input_b); break; }
            case OPERATION_XNOR   : { result = !(input_a ^  input_b); break; }
            default               : { assert(!"Unsupported operation"); break; }
        }
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
        // If current output state differs from last state...
        if (state != last && m_mappings.count(index)) {
            for (const node_map_output_t & mapping : m_mappings[index]) {
                // Is this a loopback?
                if (mapping.target_row == m_row && mapping.target_column == m_column) {
                    assert(mapping.target_is_seq);
                    m_inputs_next[mapping.target_index] = state;

                // Otherwise, send a message
                } else {
                    node_sig_state_t msg;
                    msg.header.row     = mapping.target_row;
                    msg.header.column  = mapping.target_column;
                    msg.header.command = NODE_COMMAND_SIG_STATE;
                    msg.index          = mapping.target_index;
                    msg.is_seq         = mapping.target_is_seq;
                    msg.state          = state;
                    // Dispatch the message
                    NXMessagePipe * tgt_pipe = route(msg.header.row, msg.header.column);
                    tgt_pipe->enqueue(msg);
                }
            }
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

NXMessagePipe * NXNode::route (uint32_t row, uint32_t column)
{
    // NOTE: Messages routed towards unconnected pipes will be directed to
    //       adjacent pipes in a clockwise order
    assert(!(row == m_row && column == m_column));
    NXMessagePipe * tgt_pipe = NULL;
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
