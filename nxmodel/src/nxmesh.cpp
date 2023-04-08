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

#include <assert.h>

#include <plog/Log.h>

#include "nxmesh.hpp"

using namespace NXModel;

NXMesh::NXMesh (uint32_t rows, uint32_t columns)
    : m_rows    ( rows    )
    , m_columns ( columns )
{
    // Create the nodes
    for (uint32_t row = 0; row < m_rows; row++) {
        m_nodes.push_back(new std::vector<std::shared_ptr<NXNode>>());
        for (uint32_t column = 0; column < m_columns; column++) {
            m_nodes[row]->push_back(std::make_shared<NXNode>(
                (node_id_t){ .row    = (uint8_t)row,
                             .column = (uint8_t)column }
            ));
        }
    }
    // Link nodes together
    for (uint32_t row = 0; row < m_rows; row++) {
        for (uint32_t column = 0; column < m_columns; column++) {
            std::shared_ptr<NXNode> node = (*m_nodes[row])[column];
            if (row > 0)
                node->attach(DIRECTION_NORTH, (*m_nodes[row-1])[column]->get_pipe(DIRECTION_SOUTH));
            if (row < (m_rows - 1))
                node->attach(DIRECTION_SOUTH, (*m_nodes[row+1])[column]->get_pipe(DIRECTION_NORTH));
            if (column > 0)
                node->attach(DIRECTION_WEST, (*m_nodes[row])[column-1]->get_pipe(DIRECTION_EAST));
            if (column < (m_columns - 1))
                node->attach(DIRECTION_EAST, (*m_nodes[row])[column+1]->get_pipe(DIRECTION_WEST));
        }
    }
}

void NXMesh::reset (void)
{
    for (uint32_t row = 0; row < m_rows; row++) {
        for (uint32_t column = 0; column < m_columns; column++) {
            (*m_nodes[row])[column]->reset();
        }
    }
}

std::shared_ptr<NXNode> NXMesh::get_node (NXConstants::node_id_t id)
{
    return get_node(id.row, id.column);
}

std::shared_ptr<NXNode> NXMesh::get_node (uint32_t row, uint32_t column)
{
    assert((row < m_rows) && (column < m_columns));
    return (*m_nodes[row])[column];
}

bool NXMesh::is_idle (void)
{
    bool is_idle = true;
    for (uint32_t row = 0; row < m_rows; row++) {
        for (uint32_t column = 0; column < m_columns; column++) {
            is_idle &= (*m_nodes[row])[column]->is_idle();
            if (!is_idle) {
                PLOGD << "Node " << std::dec << row << ", " << column << " is still busy";
                break;
            }
        }
        if (!is_idle) break;
    }
    return is_idle;
}

void NXMesh::step (bool trigger)
{
    for (uint32_t row = 0; row < m_rows; row++)
        for (uint32_t column = 0; column < m_columns; column++)
            (*m_nodes[row])[column]->step(trigger);
}
