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

#ifndef __NX_CONSTANTS_HPP__
#define __NX_CONSTANTS_HPP__

#include <stdint.h>

namespace Nexus {

    // =========================================================================
    // Enumerations
    // =========================================================================

    typedef enum {
        NX_CMD_LOAD_INSTR, // 0: Instruction load
        NX_CMD_MAP_OUTPUT, // 1: Output mapping
        NX_CMD_SIG_STATE,  // 2: Signal state update
        NX_CMD_NODE_CTRL   // 3: Node control
    } nx_command_t;

    typedef enum {
        NX_CTRL_ID,       // 0: Read device identifier
        NX_CTRL_VERSION,  // 1: Read hardware version (major/minor)
        NX_CTRL_PARAM,    // 2: Read back different parameters
        NX_CTRL_ACTIVE,   // 3: Set the active status of the device
        NX_CTRL_STATUS,   // 4: Read back the current status
        NX_CTRL_CYCLES,   // 5: Read current cycle counter
        NX_CTRL_INTERVAL, // 6: Set number of cycles to run for
        NX_CTRL_RESET     // 7: Trigger a soft reset of Nexus
    } nx_ctrl_command_t;

    typedef enum {
        NX_PARAM_COUNTER_WIDTH,  // 0: Width of counters in the control block
        NX_PARAM_ROWS,           // 1: Rows in the mesh
        NX_PARAM_COLUMNS,        // 2: Columns in the mesh
        NX_PARAM_NODE_INPUTS,    // 3: Inputs per node
        NX_PARAM_NODE_OUTPUTS,   // 4: Outputs per node
        NX_PARAM_NODE_REGISTERS  // 5: Internal registers per node
    } nx_ctrl_param_t;

    // =========================================================================
    // Constants
    // =========================================================================

    // Expected ID and version values
    const uint32_t NX_DEVICE_ID     = 0x4E5853; // NXS
    const uint32_t NX_VERSION_MAJOR = 0;
    const uint32_t NX_VERSION_MINOR = 1;

    // Control message header offsets
    const uint32_t NX_CTRL_HDR_COMMAND_OFFSET = 28;
    const uint32_t NX_CTRL_HDR_COMMAND_MASK   = 0x7;

    // Control message payload offsets
    const uint32_t NX_CTRL_PAYLOAD_OFFSET = 0;
    const uint32_t NX_CTRL_PAYLOAD_MASK   = (1 << NX_CTRL_HDR_COMMAND_OFFSET) - 1;
    // - Request parameters
    const uint32_t NX_CTRL_PLD_PARAM_OFFSET = 25;
    const uint32_t NX_CTRL_PLD_PARAM_MASK   = 0x7;
    // - Active parameters
    const uint32_t NX_CTRL_PLD_ACTIVE_OFFSET = 27;
    const uint32_t NX_CTRL_PLD_ACTIVE_MASK   = 0x1;

    // Mesh message header offsets
    const uint32_t NX_MESH_HDR_ROW_OFFSET     = 27;
    const uint32_t NX_MESH_HDR_ROW_MASK       = 0xF;
    const uint32_t NX_MESH_HDR_COLUMN_OFFSET  = 23;
    const uint32_t NX_MESH_HDR_COLUMN_MASK    = 0xF;
    const uint32_t NX_MESH_HDR_COMMAND_OFFSET = 21;
    const uint32_t NX_MESH_HDR_COMMAND_MASK   = 0x3;

    // Mesh message payload offsets
    const uint32_t NX_MESH_PAYLOAD_OFFSET = 0;
    const uint32_t NX_MESH_PAYLOAD_MASK   = (1 << NX_MESH_HDR_COMMAND_OFFSET) - 1;


    // =========================================================================
    // Data Structures
    // =========================================================================

    typedef struct {
        unsigned int major;
        unsigned int minor;
    } nx_version_t;

    typedef struct {
        unsigned int counter_width;
        unsigned int rows;
        unsigned int columns;
        unsigned int node_inputs;
        unsigned int node_outputs;
        unsigned int node_registers;
    } nx_parameters_t;

    typedef struct {
        bool active;
        bool seen_idle_low;
        bool first_tick;
        bool interval_set;
    } nx_status_t;

    typedef struct {
        uint32_t     row;
        uint32_t     column;
        nx_command_t command;
    } nx_msg_header_t;

    typedef struct {
        nx_msg_header_t header;
        uint32_t        payload;
    } nx_message_t;

    // =========================================================================
    // Message Encoding Functions
    // =========================================================================

    inline uint32_t nx_build_ctrl_header (
        nx_ctrl_command_t cmd
    ) {
        return (
            ((cmd & NX_CTRL_HDR_COMMAND_MASK) << NX_CTRL_HDR_COMMAND_OFFSET)
        );
    }

    inline uint32_t nx_build_ctrl (
        nx_ctrl_command_t cmd, uint32_t payload
    ) {
        return (
            nx_build_ctrl_header(cmd) |
            ((payload & NX_CTRL_PAYLOAD_MASK) << NX_CTRL_PAYLOAD_OFFSET)
        );
    }

    inline uint32_t nx_build_ctrl_req_param (nx_ctrl_param_t param)
    {
        return nx_build_ctrl(
            NX_CTRL_PARAM,
            (param & NX_CTRL_PLD_PARAM_MASK) << NX_CTRL_PLD_PARAM_OFFSET
        );
    }

    inline uint32_t nx_build_ctrl_set_interval (uint32_t interval)
    {
        return nx_build_ctrl(
            NX_CTRL_INTERVAL,
            (interval & NX_CTRL_PAYLOAD_MASK) << NX_CTRL_PAYLOAD_OFFSET
        );
    }

    inline uint32_t nx_build_ctrl_set_active (bool active)
    {
        return nx_build_ctrl(
            NX_CTRL_ACTIVE, (active ? (1 << NX_CTRL_PLD_ACTIVE_OFFSET) : 0)
        );
    }

    inline uint32_t nx_build_mesh_header (
        uint32_t row, uint32_t col, nx_command_t cmd
    ) {
        return (
            ((row & NX_MESH_HDR_ROW_MASK    ) << NX_MESH_HDR_ROW_OFFSET    ) |
            ((col & NX_MESH_HDR_COLUMN_MASK ) << NX_MESH_HDR_COLUMN_OFFSET ) |
            ((cmd & NX_MESH_HDR_COMMAND_MASK) << NX_MESH_HDR_COMMAND_OFFSET)
        );
    }

    inline uint32_t nx_build_mesh (nx_message_t msg)
    {
        return (
            nx_build_mesh_header(
                msg.header.row,
                msg.header.column,
                msg.header.command
            ) |
            ((msg.payload & NX_MESH_PAYLOAD_MASK) << NX_MESH_PAYLOAD_OFFSET)
        );
    }

    // =========================================================================
    // Message Decoding Functions
    // =========================================================================

    inline nx_version_t nx_decode_version (uint32_t raw)
    {
        nx_version_t version = {
            .major = ((raw >> 8) & 0xFF),
            .minor = ((raw >> 0) & 0xFF)
        };
        return version;
    }

    inline nx_status_t nx_decode_status (uint32_t raw)
    {
        nx_status_t status = {
            .active        = ((raw >> 3) & 0x1) != 0,
            .seen_idle_low = ((raw >> 2) & 0x1) != 0,
            .first_tick    = ((raw >> 1) & 0x1) != 0,
            .interval_set  = ((raw >> 0) & 0x1) != 0
        };
        return status;
    }

    inline nx_message_t nx_decode_mesh (uint32_t raw)
    {
        nx_msg_header_t header = {
            .row     = ((raw >> NX_MESH_HDR_ROW_OFFSET    ) & NX_MESH_HDR_ROW_MASK    ),
            .column  = ((raw >> NX_MESH_HDR_COLUMN_OFFSET ) & NX_MESH_HDR_COLUMN_MASK ),
            .command = (nx_command_t)((raw >> NX_MESH_HDR_COMMAND_OFFSET) & NX_MESH_HDR_COMMAND_MASK)
        };
        nx_message_t message = {
            .header  = header,
            .payload = ((raw >> NX_MESH_PAYLOAD_OFFSET) & NX_MESH_PAYLOAD_MASK)
        };
        return message;
    }

}

#endif // __NX_CONSTANTS_HPP__