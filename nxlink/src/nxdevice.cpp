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
#include <stdio.h>
#include <thread>
#include <unistd.h>

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
    tx_to_device(raw);
    // Pickup from monitor
    m_rx_params.wait_dequeue(raw);
    control_response_parameters_t params = unpack_control_response_parameters(
        (uint8_t *)&raw
    );
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
    tx_to_device(raw);
    // Pickup from monitor
    m_rx_status.wait_dequeue(raw);
    control_response_status_t status = unpack_control_response_status(
        (uint8_t *)&raw
    );
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

// configure
// Selectively enable/disable output messages
//
void NXLink::NXDevice::configure (
    uint8_t out_mask /* = 0xFF */,
    uint8_t en_memory /* = 0 */,
    uint8_t en_mem_wstrb /* = 0 */
) {
    uint128_t raw = 0;
    pack_control_request_configure(
        (control_request_configure_t){
            .command      = CONTROL_REQ_TYPE_CONFIGURE,
            .en_memory    = en_memory,
            .en_mem_wstrb = en_mem_wstrb,
            .output_mask  = out_mask
        },
        (uint8_t *)&raw
    );
    tx_to_device(raw);
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
    tx_to_device(raw);
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
    tx_to_device(raw);
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
    tx_to_device(raw);
}

// memory_write
// Perform a write to one of Nexus' on-board memories
//
void NXLink::NXDevice::memory_write (
    uint8_t index, uint16_t address, uint32_t data, uint8_t strobe /* = 0xF */
) {
    uint128_t raw = 0;
    pack_control_request_memory(
        (control_request_memory_t){
            .command  = CONTROL_REQ_TYPE_MEMORY,
            .memory   = index,
            .address  = address,
            .wr_n_rd  = 1,
            .wr_data  = data,
            .wr_strb  = strobe
        },
        (uint8_t *)&raw
    );
    tx_to_device(raw);
}

// memory_read
// Perform a read from one of Nexus' on-board memories
//
uint32_t NXLink::NXDevice::memory_read (uint8_t index, uint16_t address)
{
    // Request the read
    uint128_t raw = 0;
    pack_control_request_memory(
        (control_request_memory_t){
            .command  = CONTROL_REQ_TYPE_MEMORY,
            .memory   = index,
            .address  = address,
            .wr_n_rd  = 0,
            .wr_data  = 0,
            .wr_strb  = 0
        },
        (uint8_t *)&raw
    );
    tx_to_device(raw);
    // Wait for and decode the response
    m_rx_memory.wait_dequeue(raw);
    control_response_memory_t resp = unpack_control_response_memory((uint8_t *)&raw);
    return resp.rd_data;
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
    tx_to_device(to_mesh);
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

// tx_to_device
// Send an encoded item to the device.
//
void NXLink::NXDevice::tx_to_device (uint128_t msg)
{
    // Acquire mutex
    m_tx_lock.lock();
    // Create a transmit buffer
    uint8_t * tx_buffer = NULL;
    int pm_err = posix_memalign((void **)&tx_buffer, 4096, 16 + 4096);
    assert(pm_err == 0);
    assert(tx_buffer != NULL);
    memcpy((void *)tx_buffer, (void *)&msg, 16);
    // Write to the device
    ssize_t rc = write(m_tx_fh, tx_buffer, 16);
    if (rc < 0) {
        fprintf(stderr, "tx_to_device: Write failed - %li\n", rc);
        assert(!"tx_to_device: Write failed");
    }
    // Release mutex
    m_tx_lock.unlock();
}

// rx_from_device
// Continuously consume data coming from the device, separating the streams for
// different types of message.
//
void NXLink::NXDevice::rx_from_device (void)
{
    // Setup loop to read from device
    uint128_t           buffer[SLOTS_PER_PACKET];
    control_resp_type_t fmt;
    while (true) {
        // Receive the next chunk from the device
        ssize_t rc = read(m_rx_fh, (uint8_t *)buffer, SLOTS_PER_PACKET * 16);
        if (rc <= 0) continue;
        // Decode appropriately
        for (int idx_pkt = 0; idx_pkt < SLOTS_PER_PACKET; idx_pkt++) {
            fmt = (control_resp_type_t)((buffer[idx_pkt] >> 125) & 0x7);
            // If this is a padding message - stop processing this chunk
            if (fmt == CONTROL_RESP_TYPE_PADDING) break;
            // Act on the message's format
            switch (fmt) {
                case CONTROL_RESP_TYPE_OUTPUTS: {
                    // m_rx_outputs.enqueue(buffer[idx_pkt]);
                    break;
                }
                case CONTROL_RESP_TYPE_PARAMS: {
                    m_rx_params.enqueue(buffer[idx_pkt]);
                    break;
                }
                case CONTROL_RESP_TYPE_STATUS: {
                    m_rx_status.enqueue(buffer[idx_pkt]);
                    break;
                }
                case CONTROL_RESP_TYPE_FROM_MESH: {
                    uint32_t msg = (buffer[idx_pkt] >> 97) & 0x0FFFFFFF;
                    m_rx_mesh.enqueue(msg);
                    break;
                }
                case CONTROL_RESP_TYPE_MEMORY: {
                    m_rx_memory.enqueue(buffer[idx_pkt]);
                    break;
                }
                default: {
                    std::cout << "ERROR: Unknown message format " << std::dec << fmt << std::endl;
                    assert(!"Monitor received message with bad format");
                }
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

    // Build up a 96-bit mask
    uint128_t mask = 0;
    mask  |= 0xFFFFFFFF;
    mask <<= 32;
    mask  |= 0xFFFFFFFF;
    mask <<= 32;
    mask  |= 0xFFFFFFFF;

    // Run in a loop, dequeuing messages
    while (true) {
        // Attempt to dequeue the next output segment
        uint128_t raw;
        m_rx_outputs.wait_dequeue(raw);
        control_response_outputs_t msg = {
            .format  = CONTROL_RESP_TYPE_OUTPUTS,
            .stamp   = (uint32_t)((raw >> 102) & 0xFFFFFF),
            .index   = (uint8_t )((raw >>  99) & 0x7),
            .section = (raw >>   3) & mask
        };

        // Check for an illegal message
        if (msg.index >= per_cycle) {
            std::cout << "WARNING: Dropping out-of-range output received in cycle "
                      << std::dec << cycle << " for slot " << std::dec
                      << msg.index << std::endl;
            continue;

        // Check if the cycle has changed
        } else if (received > 0 && (cycle % (1 << TIMER_WIDTH)) != msg.stamp) {
            // std::cout << "WARNING: Dropping partial outputs for cycle "
            //           << std::dec << cycle << std::endl;
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
