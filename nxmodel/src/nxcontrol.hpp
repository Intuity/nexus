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
#include <memory>
#include <stdint.h>
#include <stdbool.h>

#include "nxconstants.hpp"
#include "nxcontrolpipe.hpp"
#include "nxmessagepipe.hpp"

#ifndef __NXCONTROL_HPP__
#define __NXCONTROL_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXControl {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXControl (
              unsigned int rows
            , unsigned int columns
        )   : m_rows    ( rows    )
            , m_columns ( columns )
        {
            m_to_host   = std::make_shared<NXControlPipe>();
            m_from_host = std::make_shared<NXControlPipe>();
            reset();
        }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Attach pipe towards the mesh (outbound)
         *
         * @param pipe pointer to the pipe
         */
        void attach_to_mesh (std::shared_ptr<NXMessagePipe> pipe) { m_to_mesh = pipe; }

        /** Attach pipe from the mesh (inbound)
         *
         * @param pipe pointer to the pipe
         */
        void attach_from_mesh (std::shared_ptr<NXMessagePipe> pipe) { m_from_mesh = pipe; }

        /** Resets the state of the controller
         */
        void reset (void);

        /** Determine if the controller is idle (whether there are any queued
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

        // Mesh size
        unsigned int m_rows;
        unsigned int m_columns;

        // Control pipes to/from host
        std::shared_ptr<NXControlPipe> m_to_host;
        std::shared_ptr<NXControlPipe> m_from_host;

        // Message pipes to/from mesh
        std::shared_ptr<NXMessagePipe> m_to_mesh;
        std::shared_ptr<NXMessagePipe> m_from_mesh;

    };
}

#endif // __NXCONTROL_HPP__
