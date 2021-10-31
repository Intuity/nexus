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
        for (uint32_t idx = 0; idx < 2; idx++) {
            node_loopback_t msg;
            msg.header.row     = row;
            msg.header.column  = column;
            msg.header.command = NODE_COMMAND_LOOPBACK;
            msg.select         = idx;
            msg.section        = (loopback >> (16 * idx)) & 0xFFFF;
            model->get_ingress()->enqueue(msg);
        }
        // Load instructions
        for (const auto & json_instr : node["instructions"]) {
            uint32_t instr = json_instr;
            if (verbose) {
                std::cout << "[NXLoader] Loading row: " << row
                          << ", column: " << column << ", instruction: 0x"
                          << std::hex << std::setw(8) << std::setfill('0') << instr
                          << std::dec << std::endl;
            }
            // Load over two 16-bit chunks
            for (uint32_t idx = 0; idx < 2; idx++) {
                node_load_t msg;
                msg.header.row     = row;
                msg.header.column  = column;
                msg.header.command = NODE_COMMAND_LOAD;
                msg.last           = (idx == 1);
                msg.data           = (instr >> (16 * (1 - idx))) & 0xFFFF;
                model->get_ingress()->enqueue(msg);
            }
        }
        // Set the number of instructions
        node_control_t ctrl_instr;
        ctrl_instr.header.row     = row;
        ctrl_instr.header.column  = column;
        ctrl_instr.header.command = NODE_COMMAND_CONTROL;
        ctrl_instr.param          = NODE_PARAMETER_INSTRUCTIONS;
        ctrl_instr.value          = node["instructions"].size();
        model->get_ingress()->enqueue(ctrl_instr);
        if (verbose) {
            std::cout << "[NXLoader] Setting instruction count row: " << row
                      << ", column: " << column << ", count "
                      << node["instructions"].size() << std::endl;
        }
        // Setup the output lookups
        uint32_t output_index = 0;
        uint32_t next_address = node["instructions"].size() + node["outputs"].size();
        for (const auto & outputs : node["outputs"]) {
            // Generate the lookup
            output_lookup_t lookup;
            lookup.start  = next_address;
            lookup.stop   = next_address + outputs.size() - 1;
            lookup.active = (outputs.size() > 0);
            uint32_t encoded = 0;
            pack_output_lookup(lookup, (uint8_t *)&encoded);
            if (verbose) {
                std::cout << "[NXLoader] Loading lookup - row: " << row
                          << ", column: " << column << ", start: 0x"
                          << std::hex << lookup.start << ", stop: 0x"
                          << lookup.stop << std::dec << ", active: "
                          << (lookup.active ? "YES" : "NO") << std::endl;
            }
            // Load the lookup over two steps
            for (uint32_t idx = 0; idx < 2; idx++) {
                node_load_t msg;
                msg.header.row     = row;
                msg.header.column  = column;
                msg.header.command = NODE_COMMAND_LOAD;
                msg.last           = (idx == 1);
                msg.data           = (encoded >> (16 * (1 - idx))) & 0xFFFF;
                model->get_ingress()->enqueue(msg);
            }
            // Increment to the next output
            output_index++;
            // Offset the address
            next_address += outputs.size();
        }
        // Load the output mappings
        for (const auto & outputs : node["outputs"]) {
            for (const auto & mapping : outputs) {
                // Generate the mapping
                output_mapping_t entry;
                entry.row    = mapping["row"];
                entry.column = mapping["column"];
                entry.index  = mapping["index"];
                entry.is_seq = mapping["is_seq"];
                uint32_t encoded = 0;
                pack_output_mapping(entry, (uint8_t *)&encoded);
                if (verbose) {
                    std::cout << "[NXLoader] Loading mapping - row: " << row
                              << ", column: " << column
                              << ", target row: " << (int)entry.row
                              << ", target column: " << (int)entry.column
                              << ", target index: " << (int)entry.index
                              << ", target is seq: " << (int)entry.is_seq << std::endl;
                }
                // Load the mapping over two steps
                for (uint32_t idx = 0; idx < 2; idx++) {
                    node_load_t msg;
                    msg.header.row     = row;
                    msg.header.column  = column;
                    msg.header.command = NODE_COMMAND_LOAD;
                    msg.last           = (idx == 1);
                    msg.data           = (encoded >> (16 * (1 - idx))) & 0xFFFF;
                    model->get_ingress()->enqueue(msg);
                }
            }
        }
        // Set the number of enabled outputs
        node_control_t ctrl_output;
        ctrl_output.header.row     = row;
        ctrl_output.header.column  = column;
        ctrl_output.header.command = NODE_COMMAND_CONTROL;
        ctrl_output.param          = NODE_PARAMETER_OUTPUTS;
        ctrl_output.value          = output_index;
        if (verbose) {
            std::cout << "[NXLoader] Setting output count row: " << row
                      << ", column: " << column << ", count "
                      << output_index << std::endl;
        }
        model->get_ingress()->enqueue(ctrl_output);
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
