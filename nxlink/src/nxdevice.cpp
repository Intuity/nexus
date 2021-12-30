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

#include <algorithm>
#include <assert.h>
#include <chrono>
#include <cstring>
#include <iomanip>
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
    control_response_parameters_t params = read_parameters();
    return params.id;
}

// read_version
// Read back the version information from the device
//
NXLink::nx_version_t NXLink::NXDevice::read_version (void)
{
    control_response_parameters_t params = read_parameters();
    return (nx_version_t){
        .major = params.ver_major,
        .minor = params.ver_minor
    };
}

// identify
// Read back the device identifier and major/minor version, returns TRUE if all
// values match expectation, FALSE if not. If quiet is active, log message will
// be suppressed.
//
bool NXLink::NXDevice::identify (bool quiet /* = true */)
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
// of the control_response_parameters_t struct
//
control_response_parameters_t NXLink::NXDevice::read_parameters (void)
{
    // Send a request for the device parameters
    uint128_t raw = 0;
    pack_control_request_raw(
        (control_request_raw_t){
            .command = CONTROL_REQ_TYPE_READ_PARAMS,
            .payload = 0
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(raw);
    // Pickup from monitor
    control_response_parameters_t params;
    m_rx_params.wait_dequeue(params);
    return params;
}

// read_status
// Read the current status of the device, returns a populated instance of the
// nx_status_t struct
//
control_response_status_t NXLink::NXDevice::read_status (void)
{
    // Send a request for the device parameters
    uint128_t raw = 0;
    pack_control_request_raw(
        (control_request_raw_t){
            .command = CONTROL_REQ_TYPE_READ_STATUS,
            .payload = 0
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(raw);
    // Pickup from monitor
    control_response_status_t status;
    m_rx_status.wait_dequeue(status);
    return status;
}

// read_cycles
// Read the current cycle count of the device, returns uint32_t
//
uint32_t NXLink::NXDevice::read_cycles (void)
{
    control_response_status_t status = read_status();
    return status.cycle;
}

// reset
// Send a soft reset request to the device, then wait until safe to resume
//
void NXLink::NXDevice::reset (void)
{
    // Send a request for the device parameters
    uint128_t raw = 0;
    pack_control_request_raw(
        (control_request_raw_t){
            .command = CONTROL_REQ_TYPE_SOFT_RESET,
            .payload = 1
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(raw);
    // Wait for 100ms
    std::this_thread::sleep_for(100ms);
    // Check the identity of the device
    assert(identify(true));
    // Check that the reset status is expected
    control_response_status_t status = read_status();
    assert(
        !status.active          &&
        status.first_tick       &&
        (status.cycle     == 0) &&
        (status.countdown == 0)
    );
}

// start
// Start simulation, running indefinitely or for a given number of cycles
//
void NXLink::NXDevice::start (uint32_t cycles /* = 0 */)
{
    uint128_t raw = 0;
    pack_control_request_trigger(
        (control_request_trigger_t){
            .command  = CONTROL_REQ_TYPE_TRIGGER,
            .col_mask = ((1 << MAX_COLUMN_COUNT) - 1),
            .cycles   = cycles,
            .active   = 1
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(raw);
}

// stop
// Stop simulation immediately
//
void NXLink::NXDevice::stop (void)
{
    uint128_t raw = 0;
    pack_control_request_trigger(
        (control_request_trigger_t){
            .command  = CONTROL_REQ_TYPE_TRIGGER,
            .col_mask = ((1 << MAX_COLUMN_COUNT) - 1),
            .cycles   = 0,
            .active   = 0
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(raw);
}

// send_to_mesh
// Forward a messsage through the controller into the mesh
//
void NXLink::NXDevice::send_to_mesh (uint32_t to_mesh)
{
    uint128_t raw = 0;
    pack_control_request_to_mesh(
        (control_request_to_mesh_t){
            .command = CONTROL_REQ_TYPE_TO_MESH,
            .message = to_mesh
        },
        (uint8_t *)&raw
    );
    m_pipe->tx_to_device(to_mesh);
}

// receive_from_mesh
// Receive a message from the mesh, returns true if a message is available, else
// returns false unless blocking is set in which case it will wait until data is
// available.
//
bool NXLink::NXDevice::receive_from_mesh (uint32_t & msg, bool blocking)
{
    // If nothing available to dequeue, return false
    if (!blocking && m_rx_mesh.size_approx() == 0) return false;
    // Otherwise pop the next entry
    m_rx_mesh.wait_dequeue(msg);
    // Return true to indicate a successful receive
    return true;
}

// monitor
// Continuously consume data coming from the device, separating the streams for
// different types of message.
//
void NXLink::NXDevice::monitor (void)
{
    uint128_t                    raw;
    control_response_from_mesh_t msg;
    while (true) {
        // Receive the next message from the mesh
        raw = m_pipe->rx_from_device();
        // Decode appropriately
        msg = unpack_control_response_from_mesh((uint8_t *)&raw);
        switch (msg.format) {
            case CONTROL_RESP_TYPE_OUTPUTS: {
                m_rx_outputs.enqueue(unpack_control_response_outputs((uint8_t *)&raw));
                break;
            }
            case CONTROL_RESP_TYPE_PARAMS: {
                m_rx_params.enqueue(unpack_control_response_parameters((uint8_t *)&raw));
                break;
            }
            case CONTROL_RESP_TYPE_STATUS: {
                m_rx_status.enqueue(unpack_control_response_status((uint8_t *)&raw));
                break;
            }
            case CONTROL_RESP_TYPE_FROM_MESH: {
                m_rx_mesh.enqueue(msg.message);
                break;
            }
            default: {
                std::cout << "ERROR: Unknown message format " << std::dec << msg.format << std::endl;
                assert(!"Monitor received message with bad format");
            }
        }
    }
}

// process_outputs
// Digest output messages coming from the device and accumulate the state
//
void NXLink::NXDevice::process_outputs (control_response_parameters_t params)
{
    // Determine the number of output messages per cycle
    uint32_t mesh_outs = params.columns * params.node_outs;
    uint32_t per_cycle = (mesh_outs + OUT_BITS_PER_MSG - 1) / OUT_BITS_PER_MSG;

    // Create storage for the different messages
    uint64_t cycle = 0;
    uint32_t received = 0;
    bool populated[per_cycle];
    control_response_outputs_t messages[per_cycle];
    std::fill_n(populated, per_cycle, false);

    // Run in a loop, dequeuing messages
    while (true) {
        // Attempt to dequeue the next output segment
        control_response_outputs_t msg;
        m_rx_outputs.wait_dequeue(msg);

        // Check for an illegal message
        if (msg.index >= per_cycle) {
            std::cout << "WARNING: Dropping out-of-range output received in cycle "
                      << std::dec << cycle << " for slot " << std::dec
                      << msg.index << std::endl;
            continue;

        // Check if the cycle has changed
        } else if (received > 0 && (cycle % (1 << TIMER_WIDTH)) != msg.stamp) {
            std::cout << "WARNING: Dropping partial outputs for cycle "
                      << std::dec << cycle << std::endl;
            received = 0;
            std::fill_n(populated, per_cycle, false);

        // Check for a duplicated message
        } else if (populated[msg.index]) {
            std::cout << "WARNING: Dropping duplicate output received in cycle "
                      << std::dec << cycle << " for slot " << std::dec
                      << msg.index << std::endl;
            continue;

        }

        // Hold onto this fragment
        // NOTE: By adding a delta onto cycle, this allows support of long
        //       running simulations where the hardware counter wraps
        cycle += (msg.stamp - (cycle % (1 << TIMER_WIDTH)));
        received += 1;
        populated[msg.index] = true;
        std::memcpy(
            (void *)&messages[msg.index],
            (void *)&msg,
            sizeof(control_response_outputs_t)
        );

        // When all fragments are received, accumulate the full output state
        if (received >= per_cycle) {
            // Build up the full output vector
            nx_outputs_t state = {
                .cycle = cycle,
                .state = new std::list<bool>()
            };

            // Fill in the state
            for (int idx_msg = 0; idx_msg < per_cycle; idx_msg++) {
                uint32_t base_idx = idx_msg * OUT_BITS_PER_MSG;
                for (int idx_out = 0; idx_out < OUT_BITS_PER_MSG; idx_out++) {
                    // Don't go out-of-range
                    if ((base_idx + idx_out) >= mesh_outs) break;
                    // Accumulate the output
                    state.state->push_back(
                        ((messages[idx_msg].section >> idx_out) & 1) != 0
                    );
                }
            }

            // Store the output
            m_outputs.enqueue(state);

            // Clear up ready for the next cycle
            received = 0;
            std::fill_n(populated, per_cycle, false);
        }
    }
}

// get_outputs
// Get the latest state of the output
//
bool NXLink::NXDevice::get_outputs (
    NXLink::NXDevice::nx_outputs_t & state, bool blocking
) {
    // If nothing available to dequeue, return false
    if (!blocking && m_outputs.size_approx() == 0) return false;
    // Otherwise pop the next entry
    m_outputs.wait_dequeue(state);
    // Return true to indicate a successful dequeue
    return true;
}

// log_parameters
// Log parameters read back from the device
//
void NXLink::NXDevice::log_parameters (control_response_parameters_t params)
{
    std::cout << "Device Parameters:" << std::endl;
    std::cout << " - Counter Width : " << std::dec << (int)params.timer_width << std::endl;
    std::cout << " - Mesh Rows     : " << std::dec << (int)params.rows        << std::endl;
    std::cout << " - Mesh Columns  : " << std::dec << (int)params.columns     << std::endl;
    std::cout << " - Node Inputs   : " << std::dec << (int)params.node_ins    << std::endl;
    std::cout << " - Node Outputs  : " << std::dec << (int)params.node_outs   << std::endl;
    std::cout << " - Node Registers: " << std::dec << (int)params.node_regs   << std::endl;
}

// log_status
// Log components of status read back from the device
//
void NXLink::NXDevice::log_status (control_response_status_t status)
{
    std::cout << "Device Status:" << std::endl;
    std::cout << " - Active        : " << (status.active     ? "YES" : "NO") << std::endl;
    std::cout << " - Mesh Idle     : " << (status.mesh_idle  ? "YES" : "NO") << std::endl;
    std::cout << " - Agg. Idle     : " << (status.agg_idle   ? "YES" : "NO") << std::endl;
    std::cout << " - Seen Idle Low : " << (status.seen_low   ? "YES" : "NO") << std::endl;
    std::cout << " - First Tick    : " << (status.first_tick ? "YES" : "NO") << std::endl;
    std::cout << " - Cycle         : " << std::dec << (int)status.cycle << std::endl;
    std::cout << " - Countdown     : " << std::dec << (int)status.countdown << std::endl;
}

// log_mesh_message
// Log parts of a message routed into/out of the mesh
//
void NXLink::NXDevice::log_mesh_message (node_raw_t msg)
{
    std::cout << "Mesh Message:" << std::endl;
    std::cout << " - Row    : " << std::dec << (int)msg.header.row     << std::endl;
    std::cout << " - Column : " << std::dec << (int)msg.header.column  << std::endl;
    std::cout << " - Command: " << std::dec << (int)msg.header.command << std::endl;
    std::cout << " - Payload: 0x" << std::hex << (int)msg.payload << std::endl;
}
