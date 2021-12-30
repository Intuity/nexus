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

#include "nxdevice.hpp"
#include "nxpipe.hpp"

using namespace NXLink;

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
        ("channel",  "XDMA channel for control", cxxopts::value<std::string>()->default_value("0"))
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
        << result["channel"].as<std::string>();
    std::string stream_h2c = std::string(tmp.str());
    tmp.str("");
    // - Control C2H
    tmp << result["device"].as<std::string>() << "_c2h_"
        << result["channel"].as<std::string>();
    std::string stream_c2h = std::string(tmp.str());
    tmp.str("");

    // Create pipes
    NXPipe * pipe = new NXPipe(stream_h2c, stream_c2h);

    // Create a wrapper around the device
    NXDevice * device = new NXDevice(pipe);

    // Check the identity
    if (!device->identify()) {
        fprintf(stderr, "NXDevice reported a failed identity check\n");
        return 1;
    }

    // Reset the device
    std::cout << "Resetting the device" << std::endl;
    device->reset();

    // Read back the parameters
    std::cout << "Reading back parameters" << std::endl;
    device->log_parameters(device->read_parameters());

    // Read back the current status
    std::cout << "Reading back status" << std::endl;
    device->log_status(device->read_status());

    return 0;
}
