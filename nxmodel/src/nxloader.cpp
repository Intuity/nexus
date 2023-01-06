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

#include <fstream>
#include <iomanip>
#include <plog/Log.h>

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
    unsigned int design_rows = data["rows"].get<unsigned int>();
    unsigned int design_cols = data["columns"].get<unsigned int>();
    PLOGD << "[NXLoader] Opened " << path << " - "
          << " rows: " << design_rows << ", "
          << " columns: " << design_cols;
    assert(
        (design_rows <= model->get_rows()   ) &&
        (design_cols <= model->get_columns())
    );
    // Load up all of the instructions and output mappings
    for (const auto & node : data["nodes"]) {
        unsigned int row    = node["row"].get<unsigned int>();
        unsigned int column = node["column"].get<unsigned int>();
        // Load hex file into addressed node
        std::string hex_path = node["hex"].get<std::string>();
        std::ifstream fh(hex_path, std::fstream::in);
        unsigned int instr;
        unsigned int address = 0;
        while (fh >> std::hex >> instr) {
            PLOGD << "[NXLoader] Loading row: " << row
                  << ", column: " << column
                  << ", address: 0x" << std::hex << address
                  << ", instruction: 0x"
                  << std::hex << std::setw(8) << std::setfill('0') << instr;
            // Load in four 8-bit chunks
            for (uint32_t idx = 0; idx < 4; idx++) {
                node_load_t msg;
                msg.header.target.row    = row;
                msg.header.target.column = column;
                msg.header.command       = NODE_COMMAND_LOAD;
                msg.address              = (address << 1) + (idx / 2);
                msg.slot                 = (idx % 2);
                msg.data                 = (instr >> (8 * idx)) & 0xFF;
                model->get_ingress()->enqueue(msg);
            }
            // Increment address
            address += 1;
        }
    }
    // Run the mesh until it sinks all of the queued messages
    PLOGD << "[NXLoader] All messages queued, waiting for idle";
    uint32_t steps = 0;
    while (!model->get_mesh()->is_idle()) {
        model->get_mesh()->step(false);
        steps++;
    }
    PLOGD << "[NXLoader] Ran mesh for " << steps << " steps";
    // Close the file
    fh.close();
}
