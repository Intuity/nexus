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

#include "nx_device.hpp"

using namespace std::chrono_literals;

// read_device_id
// Read back the unsigned 32-bit device identifier
//
uint32_t Nexus::NXDevice::read_device_id (void)
{
    // Send a request for the device identifier
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_ID, 0));
    // Return the response
    return m_ctrl_pipe->rx_from_device();
}

// read_version
// Read back the version information from the device
//
Nexus::nx_version_t Nexus::NXDevice::read_version (void)
{
    // Send a request for the device version
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_VERSION, 0));
    // Decode and return the response
    return nx_decode_version(m_ctrl_pipe->rx_from_device());
}

// identify
// Read back the device identifier and major/minor version, returns TRUE if all
// values match expectation, FALSE if not. If quiet is active, log message will
// be suppressed.
//
bool Nexus::NXDevice::identify (bool quiet)
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

// read_cycles
// Read the current cycle count of the device, returns uint32_t
//
uint32_t Nexus::NXDevice::read_cycles (void)
{
    // Request the status
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_CYCLES, 0));

    // Decode the result
    return m_ctrl_pipe->rx_from_device();
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

// reset
// Send a soft reset request to the device, then wait until safe to resume
//
void Nexus::NXDevice::reset (void)
{
    // Send the reset request
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_RESET, 1));
    // Wait for 100ms
    std::this_thread::sleep_for(100ms);
    // Check the identity of the device
    assert(identify(true));
    // Check that the reset status is expected
    nx_status_t status = read_status();
    assert(!status.active && status.first_tick && !status.interval_set);
    // Empty the mesh state map
    m_mesh_state.clear();
}

// set_active
// Activate/deactivate the mesh - will start/pause the simulation
void Nexus::NXDevice::set_active (bool active)
{
    m_ctrl_pipe->tx_to_device(nx_build_ctrl_set_active(active));
}

// send_to_mesh
// Send a message into the mesh
//
void Nexus::NXDevice::send_to_mesh (Nexus::nx_message_t msg)
{
    m_mesh_pipe->tx_to_device(nx_build_mesh(msg));
}

// send_to_mesh
// Send a raw message into the mesh
//
void Nexus::NXDevice::send_to_mesh (uint32_t raw)
{
    m_mesh_pipe->tx_to_device(raw);
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
    if (!blocking && m_received.size_approx() == 0) return false;
    // Otherwise pop the next entry
    m_received.wait_dequeue(msg);
    // Return true to indicate a successful receive
    return true;
}

// monitor_mesh
// Continuously consume data from the mesh, tracking the state of the device
//
void Nexus::NXDevice::monitor_mesh (void)
{
    nx_message_t msg;
    while (true) {
        // Receive the next message from the mesh
        msg = nx_decode_mesh(m_mesh_pipe->rx_from_device());
        // Decode appropriately
        switch (msg.header.command) {
            case NX_CMD_SIG_STATE: {
                nx_signal_state_t state = nx_decode_mesh_signal_state(msg);
                nx_bit_addr_t bit = {
                    .row    = msg.header.row,
                    .column = msg.header.column,
                    .index  = state.index
                };
                m_mesh_state[bit] = state.value;
            }
            default: {
                m_received.enqueue(msg);
            }
        }
    }
}

// get_output_state
// Read back the full state of the output
//
uint64_t Nexus::NXDevice::get_output_state (void)
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
