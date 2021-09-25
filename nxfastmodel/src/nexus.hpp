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

#include <filesystem>
#include <iostream>
#include <list>
#include <map>
#include <stdbool.h>
#include <stdint.h>
#include <tuple>

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

        typedef std::map<output_key_t, bool> summary_t;

        // =====================================================================
        // Constructor
        // =====================================================================

        Nexus (uint32_t rows, uint32_t columns)
            : m_rows    ( rows          )
            , m_columns ( columns       )
            , m_mesh    ( rows, columns )
        { }

        // =====================================================================
        // Public Methods
        // =====================================================================

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
        NXMesh * get_mesh (void) { return &m_mesh; }

        /** Run for a specified number of cycles
         *
         * @param cycles number of cycles to run for
         */
        void run (uint32_t cycles);

        /** Dump a VCD file
         *
         * @param path path to write the VCD to
         */
        void dump_vcd (const std::string path);

    private:

        // =====================================================================
        // Private Members
        // =====================================================================

        // Sizing
        uint32_t m_rows;
        uint32_t m_columns;

        // Mesh
        NXMesh m_mesh;

        // Track output state
        std::list<summary_t *> m_output;

    };

}

#endif // __NEXUS_HPP__
