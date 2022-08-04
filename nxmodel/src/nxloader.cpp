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

#include <iomanip>

#include "json.hpp"

#include "nxloader.hpp"
#include "nxconstants.hpp"

using namespace NXModel;

NXLoader::NXLoader(Nexus * model, std::filesystem::path path, bool verbose)
{
    load(model, path, verbose);
}

NXLoader::NXLoader(Nexus * model, std::string path, bool verbose)
{
    load(model, std::filesystem::path(path), verbose);
}

void NXLoader::load(Nexus * model, std::filesystem::path path, bool verbose)
{
    std::ifstream fh(path);
    nlohmann::json data;
    fh >> data;
    // Sanity check the design against the model
    uint32_t design_rows = data["configuration"]["rows"];
    uint32_t design_cols = data["configuration"]["columns"];
    if (verbose) {
        std::cout << "[NXLoader] Opened " << path << " - "
                  << " rows: " << design_rows << ", "
                  << " columns: " << design_cols
                  << std::endl;
    }
    assert(
        (design_rows == model->get_rows()   ) &&
        (design_cols == model->get_columns())
    );
    // Load up all of the instructions and output mappings
    for (const auto & node : data["nodes"]) {
        uint32_t row    = node["row"];
        uint32_t column = node["column"];
        // Configure loopback lines
        uint32_t loopback = node["loopback"];
        if (verbose) {
            std::cout << "[NXLoader] Setting loopback row: " << row
                      << ", column: " << column << ", loopback 0x"
                      << std::hex << (int)loopback << std::dec << std::endl;
        }
        // Load instructions
        uint32_t address = 0;
        for (const auto & json_instr : node["instructions"]) {
            uint32_t instr = json_instr;
            if (verbose) {
                std::cout << "[NXLoader] Loading row: " << row
                          << ", column: " << column << ", instruction: 0x"
                          << std::hex << std::setw(8) << std::setfill('0') << instr
                          << std::dec << std::endl;
            }
            // Load over four 8-bit chunks
            for (uint32_t idx = 0; idx < 4; idx++) {
                node_load_t msg;
                msg.header.target.row    = row;
                msg.header.target.column = column;
                msg.header.command       = NODE_COMMAND_LOAD;
                msg.address              = address;
                msg.slot                 = idx;
                msg.data                 = (instr >> (8 * idx)) & 0xFF;
                model->get_ingress()->enqueue(msg);
            }
            // Increment address
            address += 1;
        }
    }
    // Run the mesh until it sinks all of the queued messages
    uint32_t steps = 0;
    while (!model->get_mesh()->is_idle()) {
        model->get_mesh()->step(false);
        steps++;
    }
    if (verbose) {
        std::cout << "[NXLoader] Ran mesh for " << steps << " steps" << std::endl;
    }
    // Close the file
    fh.close();
}
