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

#ifndef __NX_PIPE_HPP__
#define __NX_PIPE_HPP__

#include <thread>
#include <iostream>

#include <blockingconcurrentqueue.h>

namespace Nexus {

    // NXPipe
    // Manages a single pipe (e.g. control or mesh) into Nexus, queueing
    // messages into the device and receiving messages from the device.
    //
    class NXPipe
    {
    public:
        // =====================================================================
        // Constructor
        // =====================================================================
        NXPipe(std::string h2c_path, std::string c2h_path)
            : m_h2c_path (h2c_path)
            , m_c2h_path (c2h_path)
            , m_tx_q     ()
            , m_rx_q     ()
            , m_tx_thread(&NXPipe::tx_process, this)
            , m_rx_thread(&NXPipe::rx_process, this)
        { }

        // =====================================================================
        // Public Methods
        // =====================================================================
        void     tx_to_device (uint32_t data);
        bool     rx_available (void);
        uint32_t rx_from_device (void);

    private:
        // =====================================================================
        // Private Methods
        // =====================================================================
        void tx_process (void);
        void rx_process (void);

        // =====================================================================
        // Private Members
        // =====================================================================
        std::string m_h2c_path;
        std::string m_c2h_path;

        moodycamel::BlockingConcurrentQueue<uint32_t> m_tx_q;
        moodycamel::BlockingConcurrentQueue<uint32_t> m_rx_q;

        std::thread m_tx_thread;
        std::thread m_rx_thread;

    };

}

#endif // __NX_PIPE_HPP__
