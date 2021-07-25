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
#include <iostream>

#include "nx_device.hpp"

// identify
// Read back the device identifier and major/minor version, returns TRUE if all
// values match expectation, FALSE if not
//
bool Nexus::NXDevice::identify (void)
{
    // Send a request for the device identifier
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_ID, 0));
    // Send a request for the device version
    m_ctrl_pipe->tx_to_device(nx_build_ctrl(NX_CTRL_VERSION, 0));
    // Receive device identifier
    uint32_t dev_id = m_ctrl_pipe->rx_from_device();
    // Receive device version
    uint32_t version = m_ctrl_pipe->rx_from_device();
    uint32_t ver_maj = (version >> 8) & 0xFF;
    uint32_t ver_min = (version >> 0) & 0xFF;
    // Log identifier and major/minor version
    std::cout << "NXDevice::identify - ID: 0x" << std::hex << dev_id
                        << ", Version Major: " << std::dec << ver_maj
                        << ", Version Minor: " << std::dec << ver_min
                        << std::endl;
    // Check against expected values
    return (
        (dev_id  == NX_DEVICE_ID    ) &&
        (ver_maj == NX_VERSION_MAJOR) &&
        (ver_min == NX_VERSION_MINOR)
    );
}

// read_parameters
// Read back all of the parameters from the device, returns a populated instance
// of the nx_parameters_t struct
//
Nexus::nx_parameters_t Nexus::NXDevice::read_parameters(void)
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
