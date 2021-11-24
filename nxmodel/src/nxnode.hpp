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
#include <vector>

#include "nxconstants.hpp"
#include "nxmessagepipe.hpp"

#ifndef __NXNODE_HPP__
#define __NXNODE_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXNode {
    public:

        // =====================================================================
        // Data Structures
        // =====================================================================

        typedef std::vector<uint32_t> memory_t;
        typedef std::map<uint32_t, bool> io_state_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXNode (
            uint32_t row,
            uint32_t column,
            uint32_t inputs,
            uint32_t outputs,
            bool     verbose = false
        )   : m_row         ( row     )
            , m_column      ( column  )
            , m_num_inputs  ( inputs  )
            , m_num_outputs ( outputs )
            , m_verbose     ( verbose )
            , m_seen_first  ( false   )
            , m_accumulator ( 0       )
            , m_num_instr   ( 0       )
            , m_loopback    ( 0       )
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

        /** Performs a single step of execution
         *
         * @param trigger whether this is the start of a new tick
         * @return True if the node is idle, False if still busy
         */
        void step (bool trigger);

        /** Return the contents of the memory
         *
         * @return vector of the contents of the memory
         */
        std::vector<uint32_t> get_memory (void);

        /** Retrieve current input state
         *
         * @return state of inputs in the current cycle
         */
        io_state_t get_current_inputs (void);

        /** Retrieve next input state
         *
         * @return state of inputs in the next cycle
         */
        io_state_t get_next_inputs (void);

        /** Retrieve current output state
         *
         * @return state of output in the current cycle
         */
        io_state_t get_current_outputs (void);

        /** Return the number of instructions loaded
         *
         * @return integer count of instructions
         */
        uint32_t get_instruction_count (void) { return m_num_instr; }

        /** Return the number of outputs configured
         *
         * @return integer count of outputs
         */
        uint32_t get_output_count (void) { return m_num_outputs; }

        /** Return the number of inputs configured
         *
         * @return integer count of inputs
         */
        uint32_t get_input_count (void) { return m_num_inputs; }

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

        // Verbosity
        bool m_verbose;

        // Status
        bool m_seen_first;

        // Inbound and outbound message pipes
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_inbound;
        std::array<std::shared_ptr<NXMessagePipe>, 4> m_outbound;

        // Node memory
        uint32_t m_accumulator;
        memory_t m_memory;

        // Node parameters
        uint32_t m_num_instr;
        uint32_t m_num_inputs;
        uint32_t m_num_outputs;
        uint64_t m_loopback;

        // Current state
        io_state_t m_inputs_curr;
        io_state_t m_inputs_next;
        io_state_t m_outputs;
        io_state_t m_outputs_last;

    };
}

#endif // __NXNODE_HPP__
