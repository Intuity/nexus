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
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

#include "nx_pipe.hpp"

#define NXPIPE_DEBUG(...) // printf(__VA_ARGS__)

// tx_to_device
// Queue up an item to send to the device
//
void Nexus::NXPipe::tx_to_device (uint32_t data)
{
    m_tx_q.enqueue(data);
}

// rx_available
// See if any items are present in the receive queue
//
bool Nexus::NXPipe::rx_available (void)
{
    return m_rx_q.size_approx() > 0;
}

// rx_from_device
// Dequeue an item received from the device
//
uint32_t Nexus::NXPipe::rx_from_device (void)
{
    uint32_t data = 0;
    m_rx_q.wait_dequeue(data);
    return data;
}

// tx_process
// Send queued up items to the device
//
void Nexus::NXPipe::tx_process (void)
{
    // Open a file handle (O_SYNC used to ensure flush between writes)
    int fh = open(m_h2c_path.c_str(), O_RDWR | O_SYNC);
    if (fh < 0) {
        fprintf(stderr, "Failed to open H2C: %s -> %i\n", m_h2c_path.c_str(), fh);
        assert(!"Failed to open H2C handle");
        return;
    }

    // Set the buffer size (16-byte chunk is one AXI4-stream flit)
    uint32_t buffer_size = 16;

    // Create a transmit buffer
    uint8_t * tx_buffer = NULL;
    posix_memalign((void **)&tx_buffer, 4096, buffer_size + 4096);
    assert(tx_buffer != NULL);
    memset((void *)tx_buffer, 0, buffer_size);

    // Send messages forever
    uint32_t * tx_slots = (uint32_t *)tx_buffer;
    uint32_t   slot     = 0;
    uint32_t   max_slot = buffer_size / 4;

    while (true) {
        // Dequeue the next item
        m_tx_q.wait_dequeue(tx_slots[slot]);
        // Set bit 31 to indicate this is an active slot
        tx_slots[slot] |= (1 << 31);
        NXPIPE_DEBUG("Sending %3d: 0x%08x\n", slot, tx_slots[slot]);
        // Keep track of the slot
        slot += 1;
        // If the buffer is full or the queue is empty, send to the device!
        if (slot >= max_slot || (m_tx_q.size_approx() == 0)) {
            // Write the entire 16 byte buffer to avoid uninitialised data
            ssize_t rc = write(fh, tx_buffer, buffer_size);
            if (rc < 0) {
                fprintf(stderr, "tx_process: Write failed - %li\n", rc);
                assert(!"Write to device failed");
                return;
            }
            // Clear up
            slot = 0;
            memset((void *)tx_buffer, 0, buffer_size);
        }
    }
}

// rx_process
// Receive items from the device and queue them up
//
void Nexus::NXPipe::rx_process (void)
{
    // Open a file handle
    int fh = open(m_c2h_path.c_str(), O_RDWR | O_SYNC);
    if (fh < 0) {
        fprintf(stderr, "Failed to open C2H: %s -> %i\n", m_c2h_path.c_str(), fh);
        assert(!"Failed to open C2H handle");
        return;
    }

    // Read chunk-by-chunk
    while (true) {
        // Read the 16-byte chunk
        uint32_t rx_slots[4];
        memset((void *)rx_slots, 0, 16);
        ssize_t rc = read(fh, (uint8_t *)rx_slots, 16);
        if (rc < 0) continue;
        // Start digesting messages
        for (uint32_t slot = 0; slot < 4; slot++) {
            // Skip empty slots
            if (!(rx_slots[slot] & 0x80000000)) continue;
            NXPIPE_DEBUG("Receive %3d: 0x%08x\n", slot, rx_slots[slot]);
            // Decode message
            uint32_t masked = rx_slots[slot] & 0x7FFFFFFF;
            m_rx_q.enqueue(masked);
        }
    }
}
