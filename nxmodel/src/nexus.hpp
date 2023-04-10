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

#include <filesystem>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <stdbool.h>
#include <stdint.h>
#include <tuple>

#include "nxcontrol.hpp"
#include "nxcontrolpipe.hpp"
#include "nxmesh.hpp"

#ifndef __NEXUS_HPP__
#define __NEXUS_HPP__

namespace NXModel {

    class Nexus {
    public:

        // =====================================================================
        // Data Structures
        // =====================================================================

        typedef std::tuple<uint32_t, uint32_t, uint32_t> output_key_t;

        typedef std::map<output_key_t, uint8_t> summary_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        Nexus (uint32_t rows, uint32_t columns);

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Reset the entire state of Nexus (mesh, nodes, and pipes)
         */
        void reset (void);

        /** Return the number of rows in the mesh
         *
         * @return integer number of rows
         */
        uint32_t get_rows (void) { return m_rows; }

        /** Return the number of columns in the mesh
         *
         * @return integer number of rows
         */
        uint32_t get_columns (void) { return m_columns; }

        /** Return a pointer to the mesh
         *
         * @return pointer to instance of NXMesh
         */
        std::shared_ptr<NXMesh> get_mesh (void) { return m_mesh; }

        /** Return a pointer to the pipe from the host
         *
         * @return pointer to instance of NXControlPipe
         */
        std::shared_ptr<NXControlPipe> get_from_host (void) { return m_control->get_from_host(); }

        /** Return a pointer to the pipe towards the host
         *
         * @return pointer to instance of NXControlPipe
         */
        std::shared_ptr<NXControlPipe> get_to_host (void) { return m_control->get_to_host(); }

        /** Run for a specified number of cycles
         *
         * @param cycles number of cycles to run for
         */
        void run (uint32_t cycles, bool with_trigger=true);

        /** Dump a VCD file
         *
         * @param path path to write the VCD to
         */
        void dump_vcd (const std::string path);

        /** Check if there are any output vectors available
         *
         * @return True if output is available, False otherwise
         */
        bool is_output_available (void) { return !m_output.empty(); }

        /** Pop the next output vector from the store
         *
         * @return pointer to an instance of summary_t
         */
        summary_t * pop_output (void);

    private:

        // =====================================================================
        // Private Members
        // =====================================================================

        // Sizing
        uint32_t m_rows;
        uint32_t m_columns;

        // Controller
        std::shared_ptr<NXControl> m_control;

        // Mesh
        std::shared_ptr<NXMesh> m_mesh;

        // Ingress and egress pipes
        std::shared_ptr<NXMessagePipe> m_ingress;
        std::shared_ptr<NXMessagePipe> m_egress;

        // Track output state
        std::list<summary_t *> m_output;

    };

}

#endif // __NEXUS_HPP__
