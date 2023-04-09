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

#ifndef __NXCTRLPIPE_HPP__
#define __NXCTRLPIPE_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXControlPipe {
    public:

        // =====================================================================
        // Data Structures
        // =====================================================================

        typedef struct {
            bool                is_request;
            control_req_type_t  req_type;
            control_resp_type_t resp_type;
            uint128_t           encoded;
        } entry_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXControlPipe (void) { }

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
        void enqueue (control_request_raw_t         message);
        void enqueue (control_request_configure_t   message);
        void enqueue (control_request_trigger_t     message);
        void enqueue (control_request_to_mesh_t     message);
        void enqueue (control_request_memory_t      message);
        void enqueue (control_response_raw_t        message);
        void enqueue (control_response_parameters_t message);
        void enqueue (control_response_status_t     message);
        void enqueue (control_response_outputs_t    message);
        void enqueue (control_response_from_mesh_t  message);
        void enqueue (control_response_padding_t    message);

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

        /** Returns if the next message is of a request type
         *
         * @return True if a request, false if a response
         */
        bool next_is_request (void);

        /** Returns the control request type at the head of the queue
         *
         * @return The control request type
         */
        control_req_type_t next_request_type (void);

        /** Returns the control response type at the head of the queue
         *
         * @return The control response type
         */
        control_resp_type_t next_response_type (void);

        /** Retrieve the message from the head of the queue
         *
         * @param message reference to dequeue the message into
         */
        void dequeue (control_request_raw_t         & message);
        void dequeue (control_request_configure_t   & message);
        void dequeue (control_request_trigger_t     & message);
        void dequeue (control_request_to_mesh_t     & message);
        void dequeue (control_request_memory_t      & message);
        void dequeue (control_response_raw_t        & message);
        void dequeue (control_response_parameters_t & message);
        void dequeue (control_response_status_t     & message);
        void dequeue (control_response_outputs_t    & message);
        void dequeue (control_response_from_mesh_t  & message);
        void dequeue (control_response_padding_t    & message);

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

#endif // __NXCTRLPIPE_HPP__
