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
#include <bitset>
#include <iomanip>
#include <sstream>

#include <plog/Log.h>

#include "nxisa.hpp"
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
    // Reset all state
    m_idle        = true;
    m_waiting     = true;
    m_cycle       = 0;
    m_pc          = 0;
    m_offset      = false;
    m_restart_pc  = 0;
    m_next_pc     = 0;
    m_next_offset = false;
    for (int i = 0; i < 8; i++) m_registers[i] = 0;
    m_inst_memory.clear();
    m_data_memory.clear();
    // Insert a wait operation into the bottom of instruction memory
    m_inst_memory.write(0, (
        (NXISA::OP_BRANCH << NXISA::OP_LSB  ) |
        (               0 << NXISA::PC_LSB  ) |
        (               1 << NXISA::IDLE_LSB)
    ));
}

bool NXNode::is_idle (void)
{
    return (
        (m_idle                                         ) &&
        (m_inbound[0] == NULL || m_inbound[0]->is_idle()) &&
        (m_inbound[1] == NULL || m_inbound[1]->is_idle()) &&
        (m_inbound[2] == NULL || m_inbound[2]->is_idle()) &&
        (m_inbound[3] == NULL || m_inbound[3]->is_idle())
    );
}

void NXNode::step (bool trigger)
{
    // Log on entry
    PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                 << std::dec << (unsigned int)m_id.column << ") "
          << "Step " << (trigger ? "with" : "without") << " trigger";

    // Digest inbound messages, capturing if combinational updates were received
    bool comb_ips = digest();

    // If triggered or combinational updates received, evaluate
    if (trigger || comb_ips) evaluate(trigger);
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
            node_header_t header = pipe->next_header();
            // Is the message targeted at this node?
            if (header.target.row == m_id.row && header.target.column == m_id.column) {
                switch (header.command) {
                    // LOAD: Write into the node's instruction memory
                    case NODE_COMMAND_LOAD: {
                        node_load_t msg;
                        pipe->dequeue(msg);
                        uint32_t data = msg.data;
                        data <<= msg.slot * 8;
                        uint32_t mask = 0xFF;
                        mask <<= msg.slot * 8;
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "Writing " << std::hex << data << " "
                              << "to "      << std::hex << msg.address << " "
                              << "mask "    << std::hex << mask;
                        m_inst_memory.write(msg.address, data, mask);
                        break;
                    }
                    // SIGNAL: Write into the node's data memory
                    case NODE_COMMAND_SIGNAL: {
                        node_signal_t msg;
                        pipe->dequeue(msg);
                        bool offset = m_offset;
                        switch (msg.offset) {
                            case MEMORY_OFFSET_PRESERVE:
                                break;
                            case MEMORY_OFFSET_INVERSE:
                                offset = !offset;
                                break;
                            case MEMORY_OFFSET_SET_LOW:
                                offset = false;
                                break;
                            case MEMORY_OFFSET_SET_HIGH:
                                offset = true;
                                break;
                            default:
                                assert(!"Unsupported offset");
                        }
                        uint32_t data  = msg.data;
                        uint32_t mask  = 0xFF;
                        uint32_t shift = 0;
                        if (msg.slot) shift += 16;
                        if (offset  ) shift +=  8;
                        data <<= shift;
                        mask <<= shift;
                        m_data_memory.write(msg.address, data, mask);
                        break;
                    }
                    default: assert(!"Unsupported command received");
                }

            // Otherwise, route it towards the correct node
            } else {
                route(header.target, header.command)->enqueue_raw(
                    m_inbound[idx_pipe]->dequeue_raw()
                );
            }
        }
    }

    // Return whether the current input values have been modified
    return curr_delta;
}

bool NXNode::evaluate ( bool trigger )
{
    // Should always be waiting at this point
    assert(m_waiting);

    // If evaluation caused by a global trigger, adopt next PC & offset
    if (trigger) {
        m_pc          = m_next_pc;
        m_restart_pc  = m_next_pc;
        m_offset      = m_next_offset;
        m_cycle      += 1;
        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
              << std::dec << (unsigned int)m_id.column << ") "
              << "Triggered @ 0x" << (unsigned int)m_pc << " "
              << "with offset " << (unsigned int)m_offset;
    // Otherwise restart from the PC last jumped to by a trigger event
    } else {
        m_pc = m_restart_pc;
    }

    // Always clear idle & waiting flags
    m_idle    = false;
    m_waiting = false;

    // Evaluate instructions until waiting is set
    while (!m_waiting) {
        // Fetch
        uint32_t raw = m_inst_memory.read(m_pc);

        // Decode instruction type
        NXISA::opcode_t op = (NXISA::opcode_t)NXISA::extract_op(raw);

        // Extract common fields
        uint32_t        f_src_a   = NXISA::extract_src_a(raw);
        uint32_t        f_src_b   = NXISA::extract_src_b(raw);
        uint32_t        f_src_c   = NXISA::extract_src_c(raw);
        uint32_t        f_tgt     = NXISA::extract_tgt(raw);
        uint32_t        f_slot    = NXISA::extract_slot(raw);
        uint32_t        f_address = NXISA::extract_address(raw);
        NXISA::offset_t f_offset  = (NXISA::offset_t)NXISA::extract_offset(raw);
        uint32_t        f_jump_pc = NXISA::extract_pc(raw);

        // Pickup register values
        uint8_t val_a = m_registers[f_src_a];
        uint8_t val_b = m_registers[f_src_b];
        uint8_t val_c = m_registers[f_src_c];

        // Determine offset state for this instruction
        bool offset = m_offset;
        switch (f_offset) {
            case NXISA::OFFSET_PRESERVE:
                break;
            case NXISA::OFFSET_INVERSE:
                offset = !offset;
                break;
            case NXISA::OFFSET_SET_HIGH:
                offset = true;
                break;
            case NXISA::OFFSET_SET_LOW:
                offset = false;
                break;
            default:
                assert(!"Unsupported offset");
        }

        // Work out shift based on offset state and field
        uint32_t shift = (f_slot ? 16 : 0) + (offset ? 8 : 0);

        // Perform the correct operation
        switch (op) {
            case NXISA::OP_LOAD: {
                // LOAD cannot modify the TRUTH operation's result register
                assert(f_tgt != 7);
                // Load from data memory
                uint32_t word = m_data_memory.read(f_address);
                m_registers[f_tgt] = (word >> shift) & 0xFF;
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Load from 0x" << std::hex << f_address << " "
                      << "with shift " << std::dec << shift << " "
                      << "into R" << std::hex << f_tgt
                      << " (0x" << std::hex << (unsigned int)m_registers[f_tgt]
                      << ")";
                break;
            }
            case NXISA::OP_STORE: {
                uint32_t data = val_a;
                uint32_t mask = NXISA::extract_mask(raw);
                data <<= shift;
                mask <<= shift;
                m_data_memory.write(f_address, data, mask);
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Store from R" << std::hex << f_src_a << " "
                      << "into 0x" << std::hex << f_address << " "
                      << "data=0x" << std::hex << data << " "
                      << "mask=0x" << std::hex << mask;
                break;
            }
            case NXISA::OP_BRANCH: {
                // NOTE: Not fully implemented as likely to be simplified in the
                //       final ISA as branching not required
                m_waiting     = true;
                m_idle        = (NXISA::extract_idle(raw) != 0);
                m_next_pc     = f_jump_pc;
                m_next_offset = offset;
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Branch to 0x" << std::hex << m_next_pc << " "
                      << (m_idle ? "with" : "without") << " idle";
                break;
            }
            case NXISA::OP_SEND: {
                node_signal_t msg;
                msg.header.target.row    = NXISA::extract_node_row(raw);
                msg.header.target.column = NXISA::extract_node_col(raw);
                msg.header.command       = NODE_COMMAND_SIGNAL;
                msg.address              = f_address;
                msg.slot                 = f_slot;
                msg.offset               = (NXConstants::memory_offset_t)f_offset;
                msg.data                 = val_a;
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Send 0x" << std::setw(2) << std::setfill('0')
                      << std::hex << (unsigned int)val_a << " "
                      << "to (" << std::dec << (unsigned int)msg.header.target.row
                      << ", " << std::dec << (unsigned int)msg.header.target.column
                      << ") address=0x" << std::hex << (unsigned int)msg.address
                      << ", slot=" << std::dec << (unsigned int)msg.slot
                      << ", offset=" << std::dec << (unsigned int)msg.offset;
                route(msg.header.target, NODE_COMMAND_SIGNAL)->enqueue(msg);
                break;
            }
            case NXISA::OP_TRUTH: {
                // Pickup the mux values
                uint32_t mux_a = NXISA::extract_mux_a(raw);
                uint32_t mux_b = NXISA::extract_mux_b(raw);
                uint32_t mux_c = NXISA::extract_mux_c(raw);
                // Extract the selected bit from each source
                bool bit_a = (((val_a >> mux_a) & 1) != 0);
                bool bit_b = (((val_b >> mux_b) & 1) != 0);
                bool bit_c = (((val_c >> mux_c) & 1) != 0);
                // Apply shifts to the truth table
                uint32_t raw_table = NXISA::extract_table(raw);
                uint32_t shf_table = raw_table;
                if (bit_a) shf_table >>= 1;
                if (bit_b) shf_table >>= 2;
                if (bit_c) shf_table >>= 4;
                // Determine the result
                bool result = ((shf_table & 1) != 0);
                // Shift into the result register (r7)
                m_registers[7] = (m_registers[7] << 1) | (result ? 1 : 0);
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Truth operation with table 0x"
                      << std::hex << (unsigned int)raw_table
                      << " inputs (" << std::dec
                      << bit_a << ", " << bit_b << ", " << bit_c << ") -> "
                      << (result ? "1" : "0");
                break;
            }
            case NXISA::OP_ARITH: {
                assert(!"Not yet implemented");
                break;
            }
            case NXISA::OP_SHUFFLE:
            case NXISA::OP_SHUFFLE_ALT: {
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Shuffle operation";
                // Shuffle cannot modify the TRUTH operation's result register
                assert(f_tgt != 7);
                // Extract bit selectors
                uint32_t b0 = NXISA::extract_b0(raw);
                uint32_t b1 = NXISA::extract_b1(raw);
                uint32_t b2 = NXISA::extract_b2(raw);
                uint32_t b3 = NXISA::extract_b3(raw);
                uint32_t b4 = NXISA::extract_b4(raw);
                uint32_t b5 = NXISA::extract_b5(raw);
                uint32_t b6 = NXISA::extract_b6(raw);
                uint32_t b7 = NXISA::extract_b7(raw);
                // Update target register with the selections
                m_registers[f_tgt] = (
                    (((val_a >> b0) & 1) << 0) |
                    (((val_a >> b1) & 1) << 1) |
                    (((val_a >> b2) & 1) << 2) |
                    (((val_a >> b3) & 1) << 3) |
                    (((val_a >> b4) & 1) << 4) |
                    (((val_a >> b5) & 1) << 5) |
                    (((val_a >> b6) & 1) << 6) |
                    (((val_a >> b7) & 1) << 7)
                );
                break;
            }
            default: {
                assert(!"Unsupported operation");
            }
        }

        // Increment PC
        m_pc += 1;
    }

    // If dumping enabled, write out to file
    if (m_en_dump) {
        std::stringstream fname;
        fname << "dump_" << std::dec << (unsigned int)m_id.row
                  << "_" << (unsigned int)m_id.column
                  << ".txt";
        m_data_memory.dump(fname.str(), m_cycle);
    }


    // Return whether the node is now idle
    return m_idle;
}

std::shared_ptr<NXMessagePipe> NXNode::route (
    node_id_t target, node_command_t command
) {
    // NOTE: Messages routed towards unconnected pipes will be directed to
    //       adjacent pipes in a clockwise order
    assert(target.row != m_id.row || target.column != m_id.column);
    std::shared_ptr<NXMessagePipe> tgt_pipe = NULL;
    uint32_t start;
    if      (target.column < m_id.column) start = (int)DIRECTION_WEST;
    else if (target.column > m_id.column) start = (int)DIRECTION_EAST;
    else if (target.row    < m_id.row   ) start = (int)DIRECTION_NORTH;
    else                                  start = (int)DIRECTION_SOUTH;
    for (int idx_off = 0; idx_off < 4; idx_off++) {
        uint32_t trial = (start + idx_off) % 4;
        if (m_outbound[trial] == NULL) continue;
        tgt_pipe = m_outbound[trial];
        break;
    }
    assert(tgt_pipe != NULL);
    return tgt_pipe;
}
