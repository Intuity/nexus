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
    m_idle       = true;
    m_waiting    = true;
    m_cycle      = 0;
    m_pc         = 0;
    m_slot       = false;
    m_restart_pc = 0;
    m_next_pc    = 0;
    m_next_slot  = false;
    for (int i = 0; i < 8; i++) m_registers[i] = 0;
    m_inst_memory.clear();
    m_data_memory.clear();
    // Insert a wait operation into the bottom of instruction memory
    m_inst_memory.write(0, (
        (NXISA::OP_WAIT << NXISA::OP_LSB  ) |
        (             1 << NXISA::PC0_LSB ) |
        (             1 << NXISA::IDLE_LSB)
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


    // If evaluation caused by a global trigger, adopt next PC & slot
    // NOTE: This is done before 'digest' so that 'm_slot' has the correct
    //       state for locating the next cycle's state
    if (trigger) {
        m_pc          = m_next_pc;
        m_restart_pc  = m_next_pc;
        m_slot        = m_next_slot;
        m_cycle      += 1;
        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
              << std::dec << (unsigned int)m_id.column << ") "
              << "Triggered @ 0x" << (unsigned int)m_pc << " "
              << "with slot " << (unsigned int)m_slot;
    }

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
                        uint32_t data    = msg.data;
                        uint32_t mask    = 0xFF;
                        uint32_t shift   = ((msg.address & 1) ? 16 : 0) + (msg.slot ? 8 : 0);
                        uint32_t address = (msg.address >> 1);
                        data <<= shift;
                        mask <<= shift;
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "[INSTR] Writing 0x" << std::hex << std::setw(8) << std::setfill('0') << data << " "
                                         << "to 0x"   << std::hex << address << " "
                                         << "mask 0x" << std::hex << std::setw(8) << std::setfill('0') << mask;
                        m_inst_memory.write(address, data, mask);
                        break;
                    }
                    // SIGNAL: Write into the node's data memory
                    case NODE_COMMAND_SIGNAL: {
                        node_signal_t msg;
                        pipe->dequeue(msg);
                        bool slot = m_slot;
                        switch (msg.slot) {
                            case MEMORY_SLOT_PRESERVE:
                                break;
                            case MEMORY_SLOT_INVERSE:
                                slot = !slot;
                                break;
                            case MEMORY_SLOT_LOWER:
                                slot = false;
                                break;
                            case MEMORY_SLOT_UPPER:
                                slot = true;
                                break;
                            default:
                                assert(!"Unsupported slot");
                        }
                        uint32_t data  = msg.data;
                        uint32_t shift = slot ? 8 : 0;
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "[SIGNAL] Writing 0x" << std::hex << data << " "
                                          << "to 0x"   << std::hex << msg.address << " "
                                          << "slot "   << std::dec << (uint32_t)msg.slot << " "
                                          << "(-> "    << std::dec << (slot ? 1 : 0) << ", "
                                          << std::dec << (m_slot ? 1 : 0) << ")";
                        m_data_memory.write(msg.address, data << shift, 0xFF << shift);
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

    // If not freshly triggered, restart from the last triggered PC
    if (!trigger) m_pc = m_restart_pc;

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
        // - Source & target registers
        uint32_t      f_src_a        = NXISA::extract_src_a(raw);
        uint32_t      f_src_b        = NXISA::extract_src_b(raw);
        uint32_t      f_src_c        = NXISA::extract_src_c(raw);
        uint32_t      f_tgt          = NXISA::extract_tgt(raw);
        // - Mux selectors
        uint32_t      f_mux_0        = NXISA::extract_mux_0(raw);
        uint32_t      f_mux_1        = NXISA::extract_mux_1(raw);
        uint32_t      f_mux_2        = NXISA::extract_mux_2(raw);
        uint32_t      f_mux_3        = NXISA::extract_mux_3(raw);
        uint32_t      f_mux_4        = NXISA::extract_mux_4(raw);
        uint32_t      f_mux_5        = NXISA::extract_mux_5(raw);
        uint32_t      f_mux_6        = NXISA::extract_mux_6(raw);
        uint32_t      f_mux_7        = NXISA::extract_mux_7(raw);
        // - Address components
        uint32_t      f_address_10_7 = NXISA::extract_address_10_7(raw);
        uint32_t      f_address_6_0  = NXISA::extract_address_6_0(raw);
        uint32_t      f_address      = (f_address_10_7 << 7) | f_address_6_0;
        NXISA::slot_t f_slot         = (NXISA::slot_t)NXISA::extract_slot(raw);

        // Pickup register values
        uint8_t val_a = m_registers[f_src_a];
        uint8_t val_b = m_registers[f_src_b];
        uint8_t val_c = m_registers[f_src_c];

        // Determine slot state for this instruction
        bool slot = m_slot;
        switch (f_slot) {
            case NXISA::SLOT_PRESERVE:
                break;
            case NXISA::SLOT_INVERSE:
                slot = !slot;
                break;
            case NXISA::SLOT_UPPER:
                slot = true;
                break;
            case NXISA::SLOT_LOWER:
                slot = false;
                break;
            default:
                assert(!"Unsupported slot");
        }

        // Work out shift based on slot
        uint32_t shift = slot ? 8 : 0;

        // Perform the correct operation
        switch (op) {
            case NXISA::OP_MEMORY: {
                switch ((NXISA::mem_mode_t)NXISA::extract_mode(raw)) {
                    case NXISA::MEM_LOAD: {
                        // Loads cannot modify the truth table shift register
                        assert(f_tgt != 7);
                        // Load from data memory
                        uint16_t data = m_data_memory.read(f_address);
                        m_registers[f_tgt] = (data >> shift) & 0xFF;
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "@ 0x" << std::hex << m_pc << " Load into "
                              << "R" << std::hex << (unsigned int)f_tgt << " from "
                              << "addr=0x" << std::hex << f_address << " "
                              << "slot=" << std::dec << f_slot << " "
                              << "(0x" << std::hex << (unsigned int)m_registers[f_tgt] << ")";
                        break;
                    }
                    case NXISA::MEM_STORE: {
                        uint32_t data = val_a;
                        uint32_t mask = (NXISA::extract_send_row(raw) << 4) |
                                        (NXISA::extract_send_col(raw) << 0);
                        m_data_memory.write(f_address, data << shift, mask << shift);
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "@ 0x" << std::hex << m_pc << " "
                              << "Store from R" << std::hex << (unsigned int)f_src_a << " into "
                              << "addr=0x" << std::hex << f_address << " "
                              << "data=0x" << std::hex << data << " "
                              << "slot=" << std::dec << f_slot << " "
                              << "mask=0x" << std::hex << mask;
                        break;
                    }
                    case NXISA::MEM_SEND: {
                        node_signal_t msg;
                        msg.header.target.row    = NXISA::extract_send_row(raw);
                        msg.header.target.column = NXISA::extract_send_col(raw);
                        msg.header.command       = NODE_COMMAND_SIGNAL;
                        msg.address              = f_address;
                        msg.slot                 = (NXConstants::memory_slot_t)f_slot;
                        msg.data                 = val_a;
                        PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                                     << std::dec << (unsigned int)m_id.column << ") "
                              << "@ 0x" << std::hex << m_pc << " "
                              << "Send 0x" << std::setw(2) << std::setfill('0')
                              << std::hex << (unsigned int)val_a << " "
                              << "to (" << std::dec << (unsigned int)msg.header.target.row
                              << ", " << std::dec << (unsigned int)msg.header.target.column
                              << ") address=0x" << std::hex << (unsigned int)msg.address
                              << ", slot=" << std::dec << (unsigned int)msg.slot;
                        route(msg.header.target, NODE_COMMAND_SIGNAL)->enqueue(msg);
                        break;
                    }
                    default: {
                        assert(!"Unsupported memory operation mode");
                    }
                }
                break;
            }
            case NXISA::OP_WAIT: {
                m_waiting   = true;
                m_idle      = (NXISA::extract_idle(raw) != 0);
                m_next_pc   = (NXISA::extract_pc0(raw) != 0) ? 0 : (m_pc + 1);
                m_next_slot = !m_slot;
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Waiting to go to 0x" << std::hex << m_next_pc << " "
                      << (m_idle ? "with" : "without") << " idle";
                break;
            }
            case NXISA::OP_TRUTH: {
                // Extract the selected bit from each source
                bool bit_a = (((val_a >> f_mux_0) & 1) != 0);
                bool bit_b = (((val_b >> f_mux_1) & 1) != 0);
                bool bit_c = (((val_c >> f_mux_2) & 1) != 0);
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
            case NXISA::OP_PICK: {
                // Extract mask
                uint32_t mask = NXISA::extract_mask(raw);
                // Extract upper/lower
                uint32_t upper = NXISA::extract_upper(raw);
                // Grab the 4 bits
                uint32_t b0 = (val_a >> f_mux_0) & 1;
                uint32_t b1 = (val_a >> f_mux_1) & 1;
                uint32_t b2 = (val_a >> f_mux_2) & 1;
                uint32_t b3 = (val_a >> f_mux_3) & 1;
                // Join together
                uint32_t picked = (b3 << 7) | (b2 << 6) | (b1 << 5) | (b0 << 4) |
                                  (b3 << 3) | (b2 << 2) | (b1 << 1) | (b0 << 0);
                // Log operation
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Pick - R" << std::dec << f_src_a << " "
                      << "(0x" << std::hex << (unsigned int)val_a << ") "
                      << "- P0=" << std::dec << f_mux_0 << " (0x" << std::hex << b0 << ")"
                      << ", P1=" << std::dec << f_mux_1 << " (0x" << std::hex << b1 << ")"
                      << ", P2=" << std::dec << f_mux_2 << " (0x" << std::hex << b2 << ")"
                      << ", P3=" << std::dec << f_mux_3 << " (0x" << std::hex << b3 << ") "
                      << "(data=0x" << std::hex << picked << ") "
                      << "mask=0x" << std::hex << mask << " "
                      << "bits=" << (upper ? "7:4" : "3:0") << " "
                      << "address=0x" << std::hex << (64 + f_address_6_0);
                // Align the mask
                if (upper) mask <<= 4;
                // Write to memory
                m_data_memory.write(64 + f_address_6_0,
                                    picked << shift,
                                    mask << shift);
                break;
            }
            case NXISA::OP_SHUFFLE:
            case NXISA::OP_SHUFFLE_ALT: {
                // Shuffle cannot modify the TRUTH operation's result register
                assert(f_tgt != 7);
                // Update target register with the selections
                m_registers[f_tgt] = (
                    (((val_a >> f_mux_0) & 1) << 0) |
                    (((val_a >> f_mux_1) & 1) << 1) |
                    (((val_a >> f_mux_2) & 1) << 2) |
                    (((val_a >> f_mux_3) & 1) << 3) |
                    (((val_a >> f_mux_4) & 1) << 4) |
                    (((val_a >> f_mux_5) & 1) << 5) |
                    (((val_a >> f_mux_6) & 1) << 6) |
                    (((val_a >> f_mux_7) & 1) << 7)
                );
                // Log the action
                PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
                             << std::dec << (unsigned int)m_id.column << ") "
                      << "@ 0x" << std::hex << m_pc << " "
                      << "Shuffle R" << std::dec << (unsigned int)f_src_a << " "
                      << "(value 0x" << std::hex << (unsigned int)val_a << ") "
                      << "-> R" << std::dec << (unsigned int)f_tgt << " "
                      << "B0=" << std::dec << f_mux_0 << " "
                      << "B1=" << std::dec << f_mux_1 << " "
                      << "B2=" << std::dec << f_mux_2 << " "
                      << "B3=" << std::dec << f_mux_3 << " "
                      << "B4=" << std::dec << f_mux_4 << " "
                      << "B5=" << std::dec << f_mux_5 << " "
                      << "B6=" << std::dec << f_mux_6 << " "
                      << "B7=" << std::dec << f_mux_7 << " "
                      << "(result 0x" << std::hex << (unsigned int)m_registers[f_tgt] << ")";
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
    // PLOGD << "(" << std::dec << (unsigned int)m_id.row << ", "
    //              << std::dec << (unsigned int)m_id.column << ") "
    //              << "Routing to " << std::dec << (unsigned int)target.row
    //                       << ", " << std::dec << (unsigned int)target.column;
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
