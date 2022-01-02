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

#ifndef __NX_DEVICE_HPP__
#define __NX_DEVICE_HPP__

#include <fcntl.h>
#include <list>
#include <map>
#include <mutex>
#include <thread>
#include <tuple>

#include <blockingconcurrentqueue.h>

#include "nxconstants.hpp"
#include "nxlink.hpp"

namespace NXLink {

    using namespace NXConstants;

    // NXDevice
    // Abstracted interface for interacting with Nexus hardware
    //
    class NXDevice
    {
    public:
        // =====================================================================
        // Constants
        // =====================================================================
        typedef struct {
            uint64_t          cycle;
            std::list<bool> * state;
        } nx_outputs_t;

        // =====================================================================
        // Constructor
        // =====================================================================
        NXDevice(std::string h2c_path, std::string c2h_path)
            : m_rx_outputs (          )
            , m_rx_params  (          )
            , m_rx_status  (          )
            , m_rx_mesh    (          )
            , m_rx_memory  (          )
            , m_outputs    (          )
        {
            // Open the Tx handle (O_SYNC used to ensure flush between writes)
            m_tx_fh = open(h2c_path.c_str(), O_WRONLY | O_SYNC);
            if (m_tx_fh < 0) {
                fprintf(stderr, "Failed to open H2C: %s -> %i\n", h2c_path.c_str(), m_tx_fh);
                assert(!"Failed to open H2C handle");
                return;
            }
            printf("Opened H2C: %i\n", m_tx_fh);

            // Open the Rx handle
            m_rx_fh = open(c2h_path.c_str(), O_RDONLY);
            if (m_rx_fh < 0) {
                fprintf(stderr, "Failed to open C2H: %s -> %i\n", c2h_path.c_str(), m_rx_fh);
                assert(!"Failed to open C2H handle");
                return;
            }
            printf("Opened C2H: %i\n", m_rx_fh);

            // Start the receiving thread
            m_rx_thread = new std::thread(&NXDevice::rx_from_device, this);

            // Read parameters
            control_response_parameters_t params = read_parameters();

            // Start the output processing thread
            m_out_thread = new std::thread(&NXDevice::process_outputs, this, params);
        }

        // =====================================================================
        // Public Methods
        // =====================================================================

        // Control plane
        uint32_t                      read_device_id (void);
        nx_version_t                  read_version (void);
        bool                          identify (bool quiet=true);
        control_response_parameters_t read_parameters (void);
        control_response_status_t     read_status (void);
        uint32_t                      read_cycles (void);
        void                          configure (uint8_t out_mask=0xFF,
                                                 uint8_t en_memory=0,
                                                 uint8_t en_mem_wstrb=0);
        void                          reset (void);
        void                          start (uint32_t cycles=0);
        void                          stop (void);

        // Memory interface
        void     memory_write (uint8_t index, uint16_t address, uint32_t data, uint8_t strobe=0xF);
        uint32_t memory_read  (uint8_t index, uint16_t address);

        // Mesh interface
        void send_to_mesh (uint32_t to_mesh);
        bool receive_from_mesh (uint32_t & msg, bool blocking);
        void process_outputs (control_response_parameters_t params);
        bool get_outputs (nx_outputs_t & state, bool blocking);

        // Pipe interfaces
        void tx_to_device (uint128_t msg);
        void rx_from_device (void);

        // Helper methods
        void log_parameters (control_response_parameters_t params);
        void log_status (control_response_status_t status);
        void log_mesh_message (node_raw_t msg);

    private:
        // =====================================================================
        // Private Methods
        // =====================================================================

        // =====================================================================
        // Private Members
        // =====================================================================
        // Sending mutex
        std::mutex m_tx_lock;

        // Tx/Rx file handles
        int m_tx_fh;
        int m_rx_fh;

        // Streams separated by the monitor thread
        std::thread * m_rx_thread;
        moodycamel::BlockingConcurrentQueue<uint128_t> m_rx_outputs;
        moodycamel::BlockingConcurrentQueue<uint128_t> m_rx_params;
        moodycamel::BlockingConcurrentQueue<uint128_t> m_rx_status;
        moodycamel::BlockingConcurrentQueue<uint128_t> m_rx_memory;
        moodycamel::BlockingConcurrentQueue<uint32_t>  m_rx_mesh;

        // Accumulated per-cycle outputs
        std::thread * m_out_thread;
        moodycamel::BlockingConcurrentQueue<nx_outputs_t> m_outputs;

    };

}

#endif // __NX_DEVICE_HPP__
