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

#include <iostream>
#include <queue>
#include <stdint.h>
#include <stdbool.h>

#include "nxconstants.hpp"

#ifndef __NXMSGPIPE_HPP__
#define __NXMSGPIPE_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXMessagePipe {
    public:

        // =====================================================================
        // Data Structures
        // =====================================================================

        typedef struct {
            node_header_t header;
            uint64_t      encoded;
        } entry_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXMessagePipe (void) { }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Reset the state of the pipe (dropping all contents)
         */
        void reset (void);

        /** Append a message into the pipe
         *
         * @param message the message to append
         *
         */
        void enqueue (node_load_t   message);
        void enqueue (node_signal_t message);
        void enqueue (node_output_t message);
        void enqueue (node_raw_t    message);

        /** Append an already encoded entry
         *
         * @param entry the encoded entry
         */
        void enqueue_raw (entry_t entry);

        /** Determine if the queue is idle
         *
         * @return True if idle, False if entries queued
         */
        bool is_idle (void);

        /** Returns the message type at the head of the queue
         *
         * @return The message type
         */
        node_command_t next_type (void);

        /** Returns the header at the head of the queue
         *
         * @return The header
         */
        node_header_t next_header (void);

        /** Retrieve the message from the head of the queue
         *
         * @param message reference to dequeue the message into
         */
        void dequeue (node_load_t   & message);
        void dequeue (node_signal_t & message);
        void dequeue (node_output_t & message);
        void dequeue (node_raw_t    & message);

        /** Dequeue an entry without decoding it
         *
         * @return the raw entry
         */
        entry_t dequeue_raw (void);

    private:

        // =====================================================================
        // Members
        // =====================================================================

        // Queue of messages
        std::queue<entry_t> m_messages;

    };
}

#endif // __NXMSGPIPE_HPP__
