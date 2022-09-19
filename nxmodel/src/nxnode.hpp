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

#include <array>
#include <iostream>
#include <map>
#include <memory>
#include <stdint.h>
#include <stdbool.h>
#include <queue>

#include "nxconstants.hpp"
#include "nxmemory.hpp"
#include "nxmessagepipe.hpp"

#ifndef __NXNODE_HPP__
#define __NXNODE_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXNode {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXNode (
              node_id_t id
            , bool      en_dump = false
        )   : m_id          ( id      )
            , m_en_dump     ( en_dump )
            , m_idle        ( true    )
            , m_waiting     ( true    )
            , m_cycle       ( 0       )
            , m_pc          ( 0       )
            , m_offset      ( false   )
            , m_restart_pc  ( 0       )
            , m_next_pc     ( 0       )
            , m_next_offset ( false   )
        {
            m_registers = new uint8_t[8];
            for (int i = 0; i < 4; i++) {
                m_inbound[i]  = std::make_shared<NXMessagePipe>();
                m_outbound[i] = NULL;
            }
            reset();
        }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Attach an outbound pipe
         *
         * @param dirx direction of the outbound pipe
         * @param pipe pointer to the outbound pipe
         */
        void attach (direction_t dirx, std::shared_ptr<NXMessagePipe> pipe);

        /** Get a reference to an inbound pipe
         *
         * @param dirx direction of the inbound pipe
         * @return pointer to the NXMessagePipe
         */
        std::shared_ptr<NXMessagePipe> get_pipe (direction_t dirx);

        /** Resets the state of the node
         */
        void reset (void);

        /** Determine if the node is idle (whether there are any queued messages)
         *
         * @return True if idle, False if not
         */
        bool is_idle (void);

        /** Performs a single step of execution
         *
         * @param trigger whether this is the start of a new tick
         * @return True if the node is idle, False if still busy
         */
        void step (bool trigger);

        /** Return the pointer to the instruction memory
         *
         * @return pointer to instruction memory
         */
        NXMemory * get_inst_memory ( void ) { return &m_inst_memory; }

        /** Return the pointer to the data memory
         *
         * @return pointer to data memory
         */
        NXMemory * get_data_memory ( void ) { return &m_data_memory; }

        /** Enable/disable dumping
         *
         * @param enable Enabled when True, disabled when False
         */
        void set_dumping( bool enable ) { m_en_dump = enable; }

    private:

        // =====================================================================
        // Private Methods
        // =====================================================================

        /** Digest inbound messages and update state
         *
         * @return True if current input values have changed, false otherwise
         */
        bool digest ( void );

        /** Transform inputs to outputs using instructions
         *
         * @return True if output values have changed, false otherwise
         */
        bool evaluate ( bool trigger );

        /** Return the correct target pipe for a message
         *
         * @param  target   target row
         * @param  command  Command being sent
         * @return          pointer to NXMessagePipe
         */
        std::shared_ptr<NXMessagePipe> route (
            node_id_t target, node_command_t command
        );

        // =====================================================================
        // Private Members
        // =====================================================================

        // Mesh location
        node_id_t m_id;

        // Inbound and outbound message pipes
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_inbound;
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_outbound;

        // Node memory
        NXMemory m_inst_memory;
        NXMemory m_data_memory;
        bool     m_en_dump;

        // Node state
        bool      m_idle;
        bool      m_waiting;
        uint32_t  m_cycle;
        uint32_t  m_pc;
        bool      m_offset;
        uint32_t  m_restart_pc;
        uint32_t  m_next_pc;
        bool      m_next_offset;
        uint8_t * m_registers;

    };
}

#endif // __NXNODE_HPP__
