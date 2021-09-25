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

#include <filesystem>
#include <iostream>
#include <stdint.h>
#include <string>
#include <vector>

#include <cxxopts.hpp>

#include "nexus.hpp"
#include "nxloader.hpp"

int main (int argc, char * argv []) {
    // Create instance of cxxopts
    cxxopts::Options parser(
        "nxfastmodel", "Fast non-timing accurate model of Nexus"
    );

    // Setup options
    parser.add_options()
        // Mesh sizing
        ("r,rows",    "Number of rows",    cxxopts::value<uint32_t>()->default_value("3"))
        ("c,columns", "Number of columns", cxxopts::value<uint32_t>()->default_value("3"))
        // Simulation
        ("cycles", "Number of cycles to run for", cxxopts::value<uint32_t>()->default_value("10"))
        // VCD dumping
        ("vcd", "Path to write VCD out to", cxxopts::value<std::string>())
        // Debug/verbosity
        ("v,verbose", "Enable verbose output")
        ("h,help",    "Print help and usage information");

    // Setup positional arguments
    parser.add_options()
        ("positional", "Arguments", cxxopts::value<std::vector<std::string>>());
    parser.parse_positional("positional");

    // Parse options
    auto options = parser.parse(argc, argv);

    // Detect if help was requested
    if (options.count("help")) {
        std::cout << parser.help() << std::endl;
        return 0;
    }

    // Check positionl arguments
    if (!options["positional"].count()) {
        std::cerr << "[NXFastModel] No path to design given" << std::endl;
        return 1;
    }
    auto & positional = options["positional"].as<std::vector<std::string>>();

    // Pickup sizing
    uint32_t rows    = options["rows"].as<uint32_t>();
    uint32_t columns = options["columns"].as<uint32_t>();
    std::cout << "[NXFastModel] Requested " << rows << "x" << columns << std::endl;

    // Create the Nexus model
    NXModel::Nexus * model = new NXModel::Nexus(rows, columns);

    // Load a design
    std::filesystem::path path = positional[0];
    NXModel::NXLoader loader(model, std::filesystem::canonical(path));

    // Run for the requested number of cycles
    uint32_t cycles = options["cycles"].as<uint32_t>();
    model->run(cycles);

    // Optionally write out a VCD
    if (options.count("vcd")) {
        model->dump_vcd(
            std::filesystem::absolute(options["vcd"].as<std::string>()).string()
        );
    }

    return 0;
}
