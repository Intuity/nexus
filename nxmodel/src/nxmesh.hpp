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

#include <stdint.h>

#include <memory>
#include <vector>

#include "nxnode.hpp"
#include "nxconstants.hpp"

#ifndef __NXMESH_HPP__
#define __NXMESH_HPP__

namespace NXModel {

    using namespace NXConstants;

    class NXMesh {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXMesh (uint32_t rows, uint32_t columns);

        // =====================================================================
        // Destructor
        // =====================================================================

        ~NXMesh (void)
        {
            for (uint32_t row = 0; row < m_rows; row++) delete m_nodes[row];
        }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /** Retrieve a node from the mesh
         *
         * @param  id   node identifier (carries row & column)
         * @return      pointer to the NXNode instance
         */
        std::shared_ptr<NXNode> get_node (node_id_t id);

        /** Retrieve a node from the mesh
         *
         * @param  row      row address of the node
         * @param  column   column address of the node
         * @return          pointer to the NXNode instance
         */
        std::shared_ptr<NXNode> get_node (uint32_t row, uint32_t column);

        /** Determine if the whole mesh is idle
         *
         * @return True if every node is idle, False otherwise
         */
        bool is_idle (void);

        /** Step forward every node in the mesh
         *
         * @param trigger signifies the start of a new cycle
         */
        void step (bool trigger);

    private:

        // =====================================================================
        // Private Members
        // =====================================================================

        // Sizing
        uint32_t m_rows;
        uint32_t m_columns;

        // Nodes in mesh
        std::vector<std::vector<std::shared_ptr<NXNode>> *> m_nodes;

    };

}

#endif // __NXMESH_HPP__
