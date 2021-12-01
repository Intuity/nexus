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

#include <thread>
#include <map>
#include <tuple>

#include <blockingconcurrentqueue.h>

#include "nxconstants.hpp"
#include "nxlink.hpp"
#include "nxpipe.hpp"

namespace NXLink {

    // NXDevice
    // Abstracted interface for interacting with Nexus hardware
    //
    class NXDevice
    {
    public:
        // =====================================================================
        // Constants
        // =====================================================================
        typedef struct nx_bit_addr {
            uint32_t row;
            uint32_t column;
            uint32_t index;
            bool operator == (const nx_bit_addr & other) const {
                return (
                    std::tie(row, column, index) ==
                    std::tie(other.row, other.column, other.index)
                );
            }
            bool operator < (const nx_bit_addr & other) const {
                return (
                    std::tie(row, column, index) <
                    std::tie(other.row, other.column, other.index)
                );
            }
        } nx_bit_addr_t;

        // =====================================================================
        // Constructor
        // =====================================================================
        NXDevice(NXPipe * ctrl_pipe, NXPipe * mesh_pipe)
            : m_ctrl_pipe(ctrl_pipe                    )
            , m_mesh_pipe(mesh_pipe                    )
            , m_received (                             )
            , m_rx_thread(&NXDevice::monitor_mesh, this)
        { }

        // =====================================================================
        // Public Methods
        // =====================================================================

        // Control plane
        uint32_t                      read_device_id (void);
        nx_version_t                  read_version (void);
        bool                          identify (bool quiet=false);
        nx_parameters_t               read_parameters (void);
        NXConstants::control_status_t read_status (void);
        uint32_t                      read_cycles (void);
        void                          set_interval (uint32_t interval);
        void                          clear_interval (void);
        void                          reset (void);
        void                          set_active (bool active);

        // Mesh interface
        void     send_to_mesh (uint32_t raw);
        bool     receive_from_mesh (uint32_t & msg, bool blocking);
        void     monitor_mesh (void);
        uint64_t get_output_state (void);

        // Helper methods
        void log_parameters (nx_parameters_t params);
        void log_status (NXConstants::control_status_t status);
        void log_mesh_message (NXConstants::node_raw_t msg);

    private:
        // =====================================================================
        // Private Methods
        // =====================================================================

        // =====================================================================
        // Private Members
        // =====================================================================
        NXPipe * m_ctrl_pipe;
        NXPipe * m_mesh_pipe;

        std::thread m_rx_thread;

        moodycamel::BlockingConcurrentQueue<uint32_t> m_received;

        std::map<nx_bit_addr_t, uint32_t> m_mesh_state;

    };

}

#endif // __NX_DEVICE_HPP__
