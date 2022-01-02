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

#include <chrono>
#include <stdlib.h>

#include <cxxopts.hpp>

#include "nxdevice.hpp"

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

    // Create a wrapper around the device
    NXDevice * device = new NXDevice(stream_h2c, stream_c2h);

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

    std::cout << "Disabling outputs" << std::endl;
    device->configure(0xF);

    std::cout << "Starting device" << std::endl;
    device->start((1 << TIMER_WIDTH) - 1);

    while (true) {
        std::cout << "Reading back status" << std::endl;
        control_response_status_t status = device->read_status();
        device->log_status(status);
        if (status.countdown == 0) break;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    // Perform a memory test
    std::cout << "Testing on-board memory" << std::endl;
    uint32_t mem_size = 1 << TOP_MEM_ADDR_WIDTH;
    uint32_t state[TOP_MEM_COUNT][mem_size];

    for (uint8_t mem_idx = 0; mem_idx < NXConstants::TOP_MEM_COUNT; mem_idx++) {
        std::cout << "Populating memory " << std::dec << (int)mem_idx << std::endl;
        for (uint16_t addr = 0; addr < mem_size; addr++) {
            state[mem_idx][addr] = rand();
            device->memory_write(mem_idx, addr, state[mem_idx][addr], 0xF);
        }
    }

    int mismatches = 0;
    int checked    = 0;
    for (uint8_t mem_idx = 0; mem_idx < NXConstants::TOP_MEM_COUNT; mem_idx++) {
        std::cout << "Checking memory " << std::dec << (int)mem_idx << std::endl;
        for (uint16_t addr = 0; addr < mem_size; addr++) {
            uint32_t data = device->memory_read(mem_idx, addr);
            if (data != state[mem_idx][addr]) {
                std::cout << "Mismatch on memory " << std::dec << (int)mem_idx
                          << " at address 0x" << std::hex << (uint32_t)addr
                          << " expecting 0x" << std::hex << state[mem_idx][addr]
                          << " got 0x" << std::hex << data
                          << std::endl;
                mismatches++;
            }
            checked++;
        }
    }

    assert(mismatches == 0);
    assert(checked    == (TOP_MEM_COUNT * mem_size));
    std::cout << "Finished checking " << std::dec << (int)checked << " entries"
              << std::endl;

    return 0;
}
