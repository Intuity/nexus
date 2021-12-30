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

#include "nxpipe.hpp"

#ifdef NX_EN_DEBUG
    #define NXPIPE_DEBUG(...) printf(__VA_ARGS__)
#else
    #define NXPIPE_DEBUG(...)
#endif // NX_EN_DEBUG

// tx_to_device
// Queue up an item to send to the device
//
void NXLink::NXPipe::tx_to_device (NXLink::uint128_t data)
{
    m_tx_q.enqueue(data);
}

// rx_available
// See if any items are present in the receive queue
//
bool NXLink::NXPipe::rx_available (void)
{
    return m_rx_q.size_approx() > 0;
}

// rx_from_device
// Dequeue an item received from the device
//
NXLink::uint128_t NXLink::NXPipe::rx_from_device (void)
{
    uint128_t data = 0;
    m_rx_q.wait_dequeue(data);
    return data;
}

// tx_process
// Send queued up items to the device
//
void NXLink::NXPipe::tx_process (void)
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
    int pm_err = posix_memalign((void **)&tx_buffer, 4096, buffer_size + 4096);
    assert(pm_err == 0);
    assert(tx_buffer != NULL);
    memset((void *)tx_buffer, 0, buffer_size);

    // Send messages forever
    uint128_t * tx_slots = (uint128_t *)tx_buffer;

    while (true) {
        // Dequeue next item from the queue
        m_tx_q.wait_dequeue(tx_slots[0]);
        // Log the payload being sent
        #if NX_EN_DEBUG
        uint32_t parts[4];
        parts[0] = (tx_slots[0] >>  0) & 0xFFFFFFFF;
        parts[1] = (tx_slots[0] >> 32) & 0xFFFFFFFF;
        parts[2] = (tx_slots[0] >> 64) & 0xFFFFFFFF;
        parts[3] = (tx_slots[0] >> 96) & 0xFFFFFFFF;
        printf(
            "Sending: 0x%08x_%08x_%08x_%08x\n",
            parts[3], parts[2], parts[1], parts[0]
        );
        #endif
        // Write to the device
        ssize_t rc = write(fh, tx_buffer, buffer_size);
        if (rc < 0) {
            fprintf(stderr, "tx_process: Write failed - %li\n", rc);
            assert(!"Write to device failed");
            return;
        }
    }
}

// rx_process
// Receive items from the device and queue them up
//
void NXLink::NXPipe::rx_process (void)
{
    // Open a file handle
    int fh = open(m_c2h_path.c_str(), O_RDWR | O_SYNC);
    if (fh < 0) {
        fprintf(stderr, "Failed to open C2H: %s -> %i\n", m_c2h_path.c_str(), fh);
        assert(!"Failed to open C2H handle");
        return;
    }

    // Read chunk-by-chunk
    uint128_t chunk = 0;
    while (true) {
        // Read the next message
        ssize_t rc = read(fh, (uint8_t *)&chunk, 16);
        // Ignore failed reads
        if (rc < 0) continue;
        // Debug logging
        #if NX_EN_DEBUG
        uint32_t parts[4];
        parts[0] = (chunk >>  0) & 0xFFFFFFFF;
        parts[1] = (chunk >> 32) & 0xFFFFFFFF;
        parts[2] = (chunk >> 64) & 0xFFFFFFFF;
        parts[3] = (chunk >> 96) & 0xFFFFFFFF;
        printf(
            "Receive %li: 0x%08x_%08x_%08x_%08x\n",
            rc, parts[3], parts[2], parts[1], parts[0]
        );
        #endif
        // Queue up for further processing
        m_rx_q.enqueue(chunk);
    }
}
