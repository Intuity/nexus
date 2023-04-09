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

#ifndef __NXAGGREGATOR_HPP__
#define __NXAGGREGATOR_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXAggregator {
    public:

        const unsigned int SLOTS  = 4;
        const unsigned int SLOT_W = 8;

        // =====================================================================
        // Constructor
        // =====================================================================

        NXAggregator (
              node_id_t id
        )   : m_id ( id )
        {
            m_inbound_mesh      = std::make_shared<NXMessagePipe>();
            m_inbound_neighbour = std::make_shared<NXMessagePipe>();
            m_outbound          = NULL;
            m_outputs           = new uint8_t[SLOTS];
            reset();
        }

        NXAggregator (
              uint8_t row
            , uint8_t column
        ) : NXAggregator((node_id_t){ row, column }) {}

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Change the aggregator's ID (row and column position)
         *
         * @param node_id new node ID
         */
        void set_node_id (node_id_t node_id);

        /** Change the aggregator's ID (row and column position)
         *
         * @param row    new node row
         * @param column new node column
         */
        void set_node_id (uint8_t row, uint8_t column);

        /** Attach the outbound pipe
         *
         * @param pipe pointer to the outbound pipe
         */
        void attach (std::shared_ptr<NXMessagePipe> pipe) { m_outbound = pipe; }

        /** Get a reference to the inbound pipe from the mesh
         *
         * @return pointer to the NXMessagePipe
         */
        std::shared_ptr<NXMessagePipe> get_pipe_mesh (void) { return m_inbound_mesh; }

        /** Get a reference to the inbound pipe from the neighbouring aggregator
         *
         * @return pointer to the NXMessagePipe
         */
        std::shared_ptr<NXMessagePipe> get_pipe_neighbour (void) { return m_inbound_neighbour; }

        /** Resets the state of the aggregator
         */
        void reset (void);

        /** Determine if the aggregator is idle (whether there are any queued
         *  messages)
         *
         * @return True if idle, False if not
         */
        bool is_idle (void);

        /** Performs a single step of execution
         */
        void step ();

    private:

        // =====================================================================
        // Private Methods
        // =====================================================================

        // =====================================================================
        // Private Members
        // =====================================================================

        // Mesh location
        node_id_t m_id;

        // Inbound and outbound message pipes
        std::shared_ptr<NXMessagePipe> m_inbound_mesh;
        std::shared_ptr<NXMessagePipe> m_inbound_neighbour;
        std::shared_ptr<NXMessagePipe> m_outbound;

        // Aggregator state
        uint8_t * m_outputs;

    };
}

#endif // __NXAGGREGATOR_HPP__
