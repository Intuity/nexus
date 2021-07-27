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

#include <cxxopts.hpp>

#include "nx_device.hpp"
#include "nx_pipe.hpp"

int main (int argc, char * argv [])
{
    // Create instance of cxxopts
    cxxopts::Options options(
        "nxlink",
        "Host side software for interfacing with Nexus running on an FPGA"
    );

    // Setup options
    options.add_options()
        // PCIe Interface
        ("d,device", "Path to PCIe device",      cxxopts::value<std::string>()->default_value("/dev/xdma0"))
        ("ch_mesh",  "XDMA channel for control", cxxopts::value<std::string>()->default_value("0"))
        ("ch_ctrl",  "XDMA channel for control", cxxopts::value<std::string>()->default_value("1"))
        // Debug/verbosity
        ("v,verbose", "Enable verbose output")
        ("h,help",    "Print help and usage information");

    // Parse options
    auto result = options.parse(argc, argv);

    // Detect if help was requested
    if (result.count("help")) {
        std::cout << options.help() << std::endl;
        return 0;
    }

    // Build the H2C and C2H paths
    std::stringstream tmp;
    // - Control H2C
    tmp << result["device"].as<std::string>() << "_h2c_"
        << result["ch_ctrl"].as<std::string>();
    std::string ctrl_h2c = std::string(tmp.str());
    tmp.str("");
    // - Control C2H
    tmp << result["device"].as<std::string>() << "_c2h_"
        << result["ch_ctrl"].as<std::string>();
    std::string ctrl_c2h = std::string(tmp.str());
    tmp.str("");
    // - Mesh H2C
    tmp << result["device"].as<std::string>() << "_h2c_"
        << result["ch_mesh"].as<std::string>();
    std::string mesh_h2c = std::string(tmp.str());
    tmp.str("");
    // - Mesh H2C
    tmp << result["device"].as<std::string>() << "_c2h_"
        << result["ch_mesh"].as<std::string>();
    std::string mesh_c2h = std::string(tmp.str());
    tmp.str("");

    // Create pipes for control & mesh
    Nexus::NXPipe * ctrl_pipe = new Nexus::NXPipe(ctrl_h2c, ctrl_c2h);
    Nexus::NXPipe * mesh_pipe = new Nexus::NXPipe(mesh_h2c, mesh_c2h);

    // Create a wrapper around the device
    Nexus::NXDevice * device = new Nexus::NXDevice(ctrl_pipe, mesh_pipe);

    // Check the identity
    if (!device->identify()) {
        fprintf(stderr, "NXDevice reported a failed identity check\n");
        return 1;
    }

    // Read back the parameters
    device->log_parameters(device->read_parameters());

    // Read back the current status
    device->log_status(device->read_status());

    // Route a message through the mesh
    Nexus::nx_message_t tx_msg;
    tx_msg.header.row     = 10;
    tx_msg.header.column  = 10;
    tx_msg.header.command = Nexus::NX_CMD_NODE_CTRL;
    tx_msg.payload        = 0x123456;
    device->send_to_mesh(tx_msg);

    // Receive a message from the mesh
    Nexus::nx_message_t rx_msg;
    memset(&rx_msg, 0, sizeof(Nexus::nx_message_t));
    device->receive_from_mesh(rx_msg, true);
    std::cout << "Received message from mesh" << std::endl;
    device->log_mesh_message(rx_msg);

    // Read back the current status
    device->log_status(device->read_status());

    // Set an interval
    device->set_interval(10);
    device->log_status(device->read_status());
    device->clear_interval();
    device->log_status(device->read_status());

    return 0;
}

