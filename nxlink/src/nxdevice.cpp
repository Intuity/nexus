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

#include <assert.h>
#include <chrono>
#include <iostream>
#include <thread>

#include "nxdevice.hpp"

using namespace std::chrono_literals;
using namespace NXConstants;

// read_device_id
// Read back the unsigned 32-bit device identifier
//
uint32_t NXLink::NXDevice::read_device_id (void)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_ID, .payload = 0},
        (uint8_t *)&raw
    );
    // Send a request for the device identifier
    m_ctrl_pipe->tx_to_device(raw);
    // Return the response
    return m_ctrl_pipe->rx_from_device();
}

// read_version
// Read back the version information from the device
//
NXLink::nx_version_t NXLink::NXDevice::read_version (void)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_VERSION, .payload = 0},
        (uint8_t *)&raw
    );
    // Send a request for the device version
    m_ctrl_pipe->tx_to_device(raw);
    // Decode and return the response
    uint32_t resp = m_ctrl_pipe->rx_from_device();
    return (nx_version_t){
        .major = ((resp >> 8) & 0xFF),
        .minor = ((resp >> 0) & 0xFF)
    };
}

// identify
// Read back the device identifier and major/minor version, returns TRUE if all
// values match expectation, FALSE if not. If quiet is active, log message will
// be suppressed.
//
bool NXLink::NXDevice::identify (bool quiet)
{
    // Get ID and version
    uint32_t     device_id = read_device_id();
    nx_version_t version   = read_version();
    // Log identifier and major/minor version
    if (!quiet) {
        std::cout << "NXDevice::identify - ID: 0x" << std::hex << device_id
                            << ", Version Major: " << std::dec << version.major
                            << ", Version Minor: " << std::dec << version.minor
                            << std::endl;
    }
    // Check against expected values
    return (
        (device_id     == HW_DEV_ID   ) &&
        (version.major == HW_VER_MAJOR) &&
        (version.minor == HW_VER_MINOR)
    );
}

// read_parameters
// Read back all of the parameters from the device, returns a populated instance
// of the nx_parameters_t struct
//
NXLink::nx_parameters_t NXLink::NXDevice::read_parameters (void)
{
    // Request each of the parameters in turn
    for (
        uint32_t param = CONTROL_PARAM_COUNTER_WIDTH;
        param <= CONTROL_PARAM_NODE_REGISTERS;
        param++
    ) {
        uint32_t raw = 0;
        pack_control_read_param(
            (control_read_param_t){
                .command = CONTROL_COMMAND_PARAM,
                .param   = (control_param_t)param
            },
            (uint8_t *)&raw
        );
        m_ctrl_pipe->tx_to_device(raw);
    }

    // Populate the parameters struct with each returned value
    nx_parameters_t params = {
        .counter_width  = m_ctrl_pipe->rx_from_device(),
        .rows           = m_ctrl_pipe->rx_from_device(),
        .columns        = m_ctrl_pipe->rx_from_device(),
        .node_inputs    = m_ctrl_pipe->rx_from_device(),
        .node_outputs   = m_ctrl_pipe->rx_from_device(),
        .node_registers = m_ctrl_pipe->rx_from_device()
    };

    // Return the populated struct
    return params;
}

// read_status
// Read the current status of the device, returns a populated instance of the
// nx_status_t struct
//
control_status_t NXLink::NXDevice::read_status (void)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_STATUS, .payload = 0},
        (uint8_t *)&raw
    );

    // Request the status
    m_ctrl_pipe->tx_to_device(raw);

    // Decode the result
    uint32_t raw_resp = m_ctrl_pipe->rx_from_device();
    return unpack_control_status((uint8_t *)&raw_resp);
}

// read_cycles
// Read the current cycle count of the device, returns uint32_t
//
uint32_t NXLink::NXDevice::read_cycles (void)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_CYCLES, .payload = 0},
        (uint8_t *)&raw
    );

    // Request the status
    m_ctrl_pipe->tx_to_device(raw);

    // Decode the result
    return m_ctrl_pipe->rx_from_device();
}

// set_interval
// Setup the simulation interval (in clock cycles)
//
void NXLink::NXDevice::set_interval (uint32_t interval)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_INTERVAL, .payload = interval },
        (uint8_t *)&raw
    );

    // Send the message
    m_ctrl_pipe->tx_to_device(raw);
}

// clear_interval
// Clear the simulation interval (by setting it to 0)
//
void NXLink::NXDevice::clear_interval (void)
{
    set_interval(0);
}

// reset
// Send a soft reset request to the device, then wait until safe to resume
//
void NXLink::NXDevice::reset (void)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_raw(
        (control_raw_t){ .command = CONTROL_COMMAND_RESET, .payload = 1 },
        (uint8_t *)&raw
    );
    // Send the reset request
    m_ctrl_pipe->tx_to_device(raw);
    // Wait for 100ms
    std::this_thread::sleep_for(100ms);
    // Check the identity of the device
    assert(identify(true));
    // Check that the reset status is expected
    control_status_t status = read_status();
    assert(!status.active && status.first_tick && !status.interval_set);
    // Empty the mesh state map
    m_mesh_state.clear();
}

// set_active
// Activate/deactivate the mesh - will start/pause the simulation
void NXLink::NXDevice::set_active (bool active)
{
    // Generate the message
    uint32_t raw = 0;
    pack_control_set_active(
        (control_set_active_t){
            .command = CONTROL_COMMAND_ACTIVE,
            .active  = (uint8_t)(active ? 1 : 0)
        },
        (uint8_t *)&raw
    );
    // Send the message
    m_ctrl_pipe->tx_to_device(raw);
}

// send_to_mesh
// Send a raw message into the mesh
//
void NXLink::NXDevice::send_to_mesh (uint32_t raw)
{
    m_mesh_pipe->tx_to_device(raw);
}

// receive_from_mesh
// Receive a message from the mesh, returns true if a message is available, else
// returns false unless blocking is set in which case it will wait until data is
// available.
//
bool NXLink::NXDevice::receive_from_mesh (uint32_t & msg, bool blocking)
{
    // If nothing available to dequeue, return false
    if (!blocking && m_received.size_approx() == 0) return false;
    // Otherwise pop the next entry
    m_received.wait_dequeue(msg);
    // Return true to indicate a successful receive
    return true;
}

// monitor_mesh
// Continuously consume data from the mesh, tracking the state of the device
//
void NXLink::NXDevice::monitor_mesh (void)
{
    uint32_t      raw;
    node_signal_t msg;
    while (true) {
        // Receive the next message from the mesh
        raw = m_mesh_pipe->rx_from_device();
        // Decode appropriately
        msg = unpack_node_signal((uint8_t *)&raw);
        switch (msg.header.command) {
            case NODE_COMMAND_SIGNAL: {
                nx_bit_addr_t bit = {
                    .row    = msg.header.row,
                    .column = msg.header.column,
                    .index  = msg.index
                };
                m_mesh_state[bit] = msg.state;
            }
            default: {
                m_received.enqueue(raw);
            }
        }
    }
}

// get_output_state
// Read back the full state of the output
//
uint64_t NXLink::NXDevice::get_output_state (void)
{
    nx_parameters_t params = read_parameters();
    std::map<nx_bit_addr_t, uint32_t>::iterator it;
    uint64_t vector = 0;
    for (it = m_mesh_state.begin(); it != m_mesh_state.end(); it++) {
        nx_bit_addr_t bit = it->first;
        uint32_t      val = it->second;
        uint32_t offset = (
            ((bit.row - params.rows) * params.columns * params.node_inputs) +
            (bit.column * params.node_inputs) +
            bit.index
        );
        vector |= val << offset;
    }
    return vector;
}

// log_parameters
// Log parameters read back from the device
//
void NXLink::NXDevice::log_parameters (NXLink::nx_parameters_t params)
{
    std::cout << "Device Parameters:" << std::endl;
    std::cout << " - Counter Width : " << std::dec << params.counter_width  << std::endl;
    std::cout << " - Mesh Rows     : " << std::dec << params.rows           << std::endl;
    std::cout << " - Mesh Columns  : " << std::dec << params.columns        << std::endl;
    std::cout << " - Node Inputs   : " << std::dec << params.node_inputs    << std::endl;
    std::cout << " - Node Outputs  : " << std::dec << params.node_outputs   << std::endl;
    std::cout << " - Node Registers: " << std::dec << params.node_registers << std::endl;
}

// log_status
// Log components of status read back from the device
//
void NXLink::NXDevice::log_status (control_status_t status)
{
    std::cout << "Device Status:" << std::endl;
    std::cout << " - Active        : " << (status.active       ? "YES" : "NO") << std::endl;
    std::cout << " - Seen Idle Low : " << (status.idle_low     ? "YES" : "NO") << std::endl;
    std::cout << " - First Tick    : " << (status.first_tick   ? "YES" : "NO") << std::endl;
    std::cout << " - Interval Set  : " << (status.interval_set ? "YES" : "NO") << std::endl;
}

// log_mesh_message
// Log parts of a message routed into/out of the mesh
//
void NXLink::NXDevice::log_mesh_message (node_raw_t msg)
{
    std::cout << "Mesh Message:" << std::endl;
    std::cout << " - Row    : " << std::dec << msg.header.row     << std::endl;
    std::cout << " - Column : " << std::dec << msg.header.column  << std::endl;
    std::cout << " - Command: " << std::dec << msg.header.command << std::endl;
    std::cout << " - Payload: 0x" << std::hex << msg.payload << std::endl;
}
