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
#include <list>
#include <map>
#include <memory>
#include <stdint.h>
#include <stdbool.h>

#include "nxconstants.hpp"
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

        NXNode (uint32_t row, uint32_t column)
            : m_row        ( row    )
            , m_column     ( column )
            , m_seen_first ( false  )
        {
            for (int i = 0; i < 4; i++) {
                m_inbound[i]  = std::make_shared<NXMessagePipe>();
                m_outbound[i] = NULL;
            }
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

        /** Appends an instruction to the internal store
         *
         * @param instruction encoded instruction to append
         */
        void append (instruction_t instr);

        /** Performs a single step of execution
         *
         * @param trigger whether this is the start of a new tick
         * @return True if the node is idle, False if still busy
         */
        void step (bool trigger);

    private:

        // =====================================================================
        // Private Methods
        // =====================================================================

        /** Digest inbound messages and update state
         *
         * @return True if current input values have changed, false otherwise
         */
        bool digest (void);

        /** Transform inputs to outputs using instructions
         *
         * @return True if output values have changed, false otherwise
         */
        bool evaluate (void);

        /** Send outbound messages
         */
        void transmit (void);

        /** Get input value
         *
         * @param index input value to retrieve
         * @return the boolean value
         */
        bool get_input (uint32_t index);

        /** Get output value
         *
         * @param index output value to retrieve
         * @return the boolean value
         */
        bool get_output (uint32_t index);

        /** Return the correct target pipe for a message
         *
         * @param row target row
         * @param column target column
         * @return pointer to NXMessagePipe
         */
        std::shared_ptr<NXMessagePipe> route (uint32_t row, uint32_t column);

        // =====================================================================
        // Private Members
        // =====================================================================

        // Mesh location
        uint32_t m_row;
        uint32_t m_column;

        // Status
        bool m_seen_first;

        // Inbound and outbound message pipes
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_inbound;
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_outbound;

        // Instruction store
        typedef std::list<instruction_t> instrs_t;
        instrs_t m_instructions;

        // Output mappings
        std::map<uint32_t, std::list<node_map_output_t>> m_mappings;

        // Current state
        typedef std::map<uint32_t, bool> io_state_t;
        io_state_t m_inputs_curr;
        io_state_t m_inputs_next;
        io_state_t m_outputs;
        io_state_t m_outputs_last;

    };
}

#endif // __NXNODE_HPP__
