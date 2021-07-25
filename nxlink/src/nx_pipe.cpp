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
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

#include "nx_pipe.hpp"

// tx_to_device: Queue up an item to send to the device
//
void Nexus::NXPipe::tx_to_device (uint32_t data)
{
    m_tx_q.enqueue(data);
}

// rx_available: See if any items are present in the receive queue
//
bool Nexus::NXPipe::rx_available (void)
{
    return m_rx_q.size_approx() > 0;
}

// rx_from_device: Dequeue an item received from the device
//
uint32_t Nexus::NXPipe::rx_from_device (void)
{
    uint32_t data = 0;
    m_rx_q.wait_dequeue(data);
    return data;
}

// tx_process: Send queued up items to the device
//
void Nexus::NXPipe::tx_process (void)
{
    // Open a file handle
    int fh = open(m_h2c_path.c_str(), O_RDWR);
    if (fh < 0) {
        fprintf(stderr, "Failed to open H2C: %s -> %i\n", m_h2c_path.c_str(), fh);
        assert(!"Failed to open H2C handle");
        return;
    }

    // Set the buffer size
    uint32_t buffer_size = 1024;

    // Create a transmit buffer
    uint8_t * tx_buffer = NULL;
    posix_memalign((void **)&tx_buffer, 4096, buffer_size + 4096);
    assert(tx_buffer != NULL);
    memset((void *)tx_buffer, 0, buffer_size);

    // Send messages forever
    uint32_t * tx_slots = (uint32_t *)tx_buffer;
    uint32_t   slot     = 0;
    uint32_t   max_slot = buffer_size / 32;
    while (true) {
        // Dequeue the next item
        m_tx_q.wait_dequeue(tx_slots[slot]);
        // Set bit 31 to indicate this is an active slot
        tx_slots[slot] |= (1 << 31);
        // Keep track of the slot
        slot += 1;
        // If the buffer is full or the queue is empty, send to the device!
        if (slot >= max_slot || (m_tx_q.size_approx() == 0)) {
            // Seek to start of device
            ssize_t rc;
            rc = lseek(fh, 0, SEEK_SET);
            if (rc != 0) {
                fprintf(stderr, "tx_process: Seek to 0 failed - %li\n", rc);
                assert(!"Failed to seek");
                return;
            }
            // Write
            rc = write(fh, tx_buffer, slot * 4);
            if (rc < 0) {
                fprintf(stderr, "tx_process: Write failed - %li\n", rc);
                assert(!"Write to device failed");
                return;
            }
            // Clear up
            slot = 0;
        }
    }
}

// rx_process: Receive items from the device and queue them up
void Nexus::NXPipe::rx_process (void)
{
    // Open a file handle
    int fh = open(m_c2h_path.c_str(), O_RDWR);
    if (fh < 0) {
        fprintf(stderr, "Failed to open C2H: %s -> %i\n", m_c2h_path.c_str(), fh);
        assert(!"Failed to open C2H handle");
        return;
    }

    // Setup a timeout on the device
    struct termios termios;
    tcgetattr(fh, &termios);
    termios.c_lflag     &= ~ICANON; // Non-canonical mode
    termios.c_cc[VTIME]  = 1;       // Timeout of 0.1 seconds
    termios.c_cc[VMIN]   = 0;
    tcsetattr(fh, TCSANOW, &termios);

    // Set the buffer size
    uint32_t buffer_size = 1024;

    // Create a receive buffer
    uint8_t * rx_buffer = NULL;
    posix_memalign((void **)&rx_buffer, 4096, buffer_size + 4096);
    assert(rx_buffer != NULL);
    memset((void *)rx_buffer, 0, buffer_size);

    // Continuously read in chunks of 64 bytes (up to 16 messages)
    uint32_t * rx_slots = (uint32_t *)rx_buffer;
    uint32_t   offset   = 0;
    while (true) {
        // Seek to the start of the device
        ssize_t rc;
        rc = lseek(fh, 0, SEEK_SET);
        if (rc != 0) {
            fprintf(stderr, "rx_process: Seek to 0 failed - %li\n", rc);
            assert(!"Failed to seek");
            return;
        }
        // Read the next message
        rc = read(fh, &rx_buffer[offset], 64);
        if (rc < 0) {
            fprintf(stderr, "rx_process: Read failed - %li\n", rc);
            assert(!"Read from device failed");
            return;
        }
        // Start digesting messages
        uint32_t slot = 0;
        while (rc >= 4) {
            // Check if this slot if populated
            if (rx_slots[slot] & 0x80000000) {
                uint32_t masked = rx_slots[slot] & 0x7FFFFFFF;
                m_rx_q.enqueue(masked);
            }
            // Keep track of the active slot
            slot += 1;
        }
        // Keep track of the remainder for the next receive
        offset = rc - (slot * 4);
    }
}
