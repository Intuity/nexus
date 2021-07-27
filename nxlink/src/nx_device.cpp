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
#include <iostream>

#include "nx_device.hpp"

// identify
// Read back the device identifier and major/minor version, returns TRUE if all
// values match expectation, FALSE if not
//
bool Nexus::NXDevice::identify (void)
{
    // Send a request for the device identifier
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_ID, 0));
    // Send a request for the device version
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_VERSION, 0));
    // Receive device identifier
    uint32_t device_id = m_ctrl_pipe->rx_from_device();
    // Receive device version
    nx_version_t version = nx_decode_version(m_ctrl_pipe->rx_from_device());
    // Log identifier and major/minor version
    std::cout << "NXDevice::identify - ID: 0x" << std::hex << device_id
                        << ", Version Major: " << std::dec << version.major
                        << ", Version Minor: " << std::dec << version.minor
                        << std::endl;
    // Check against expected values
    return (
        (device_id     == NX_DEVICE_ID    ) &&
        (version.major == NX_VERSION_MAJOR) &&
        (version.minor == NX_VERSION_MINOR)
    );
}

// read_parameters
// Read back all of the parameters from the device, returns a populated instance
// of the nx_parameters_t struct
//
Nexus::nx_parameters_t Nexus::NXDevice::read_parameters (void)
{
    // Request each of the parameters in turn
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_COUNTER_WIDTH));
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_ROWS));
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_COLUMNS));
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_NODE_INPUTS));
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_NODE_OUTPUTS));
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_req_param(NX_PARAM_NODE_REGISTERS));

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
Nexus::nx_status_t Nexus::NXDevice::read_status (void)
{
    // Request the status
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_STATUS, 0));

    // Decode the result
    return nx_decode_status(m_ctrl_pipe->rx_from_device());
}

// set_interval
// Setup the simulation interval (in clock cycles)
//
void Nexus::NXDevice::set_interval (uint32_t interval)
{
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_set_interval(interval));
}

// clear_interval
// Clear the simulation interval (by setting it to 0)
//
void Nexus::NXDevice::clear_interval (void)
{
    set_interval(0);
}

// send_to_mesh
// Send a message into the mesh
//
void Nexus::NXDevice::send_to_mesh (Nexus::nx_message_t msg)
{
    m_mesh_pipe->tx_to_device(nx_build_mesh(msg));
}

// receive_from_mesh
// Receive a message from the mesh, returns true if a message is available, else
// returns false unless blocking is set in which case it will wait until data is
// available.
//
bool Nexus::NXDevice::receive_from_mesh (
    Nexus::nx_message_t & msg, bool blocking
) {
    // If nothing available to dequeue, return false
    if (!m_mesh_pipe->rx_available() && !blocking) return false;
    // Otherwise decode
    msg = nx_decode_mesh(m_mesh_pipe->rx_from_device());
    // Return true to indicate a successful receive
    return true;
}

// log_parameters
// Log parameters read back from the device
//
void Nexus::NXDevice::log_parameters (Nexus::nx_parameters_t params)
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
void Nexus::NXDevice::log_status (Nexus::nx_status_t status)
{
    std::cout << "Device Status:" << std::endl;
    std::cout << " - Active        : " << (status.active        ? "YES" : "NO") << std::endl;
    std::cout << " - Seen Idle Low : " << (status.seen_idle_low ? "YES" : "NO") << std::endl;
    std::cout << " - First Tick    : " << (status.first_tick    ? "YES" : "NO") << std::endl;
    std::cout << " - Interval Set  : " << (status.interval_set  ? "YES" : "NO") << std::endl;
}

// log_mesh_message
// Log parts of a message routed into/out of the mesh
//
void Nexus::NXDevice::log_mesh_message (Nexus::nx_message_t msg)
{
    std::cout << "Mesh Message:" << std::endl;
    std::cout << " - Row    : " << std::dec << msg.header.row     << std::endl;
    std::cout << " - Column : " << std::dec << msg.header.column  << std::endl;
    std::cout << " - Command: " << std::dec << msg.header.command << std::endl;
    std::cout << " - Payload: 0x" << std::hex << msg.payload << std::endl;
}
