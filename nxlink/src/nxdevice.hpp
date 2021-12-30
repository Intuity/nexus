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

#include <list>
#include <map>
#include <thread>
#include <tuple>

#include <blockingconcurrentqueue.h>

#include "nxconstants.hpp"
#include "nxlink.hpp"
#include "nxpipe.hpp"

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
        NXDevice(NXPipe * pipe)
            : m_pipe       ( pipe )
            , m_rx_outputs (      )
            , m_rx_params  (      )
            , m_rx_status  (      )
            , m_rx_mesh    (      )
            , m_outputs    (      )
        {
            // Start the receiving thread
            m_rx_thread = new std::thread(&NXDevice::monitor, this);
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
        void                          reset (void);
        void                          start (uint32_t cycles=0);
        void                          stop (void);

        // Mesh interface
        void send_to_mesh (uint32_t to_mesh);
        bool receive_from_mesh (uint32_t & msg, bool blocking);
        void monitor (void);
        void process_outputs (control_response_parameters_t params);
        bool get_outputs (nx_outputs_t & state, bool blocking);

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
        NXPipe * m_pipe;

        // Streams separated by the monitor thread
        std::thread * m_rx_thread;
        moodycamel::BlockingConcurrentQueue<control_response_outputs_t>    m_rx_outputs;
        moodycamel::BlockingConcurrentQueue<control_response_parameters_t> m_rx_params;
        moodycamel::BlockingConcurrentQueue<control_response_status_t>     m_rx_status;
        moodycamel::BlockingConcurrentQueue<uint32_t>                      m_rx_mesh;

        // Accumulated per-cycle outputs
        std::thread * m_out_thread;
        moodycamel::BlockingConcurrentQueue<nx_outputs_t> m_outputs;

    };

}

#endif // __NX_DEVICE_HPP__
