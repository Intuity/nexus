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

#include "json.hpp"

#include "nxloader.hpp"
#include "nxconstants.hpp"

using namespace NXModel;

NXLoader::NXLoader(Nexus * model, std::filesystem::path path)
{
    std::ifstream fh(path);
    nlohmann::json data;
    fh >> data;
    // Sanity check the design against the model
    uint32_t design_rows = data["configuration"]["rows"];
    uint32_t design_cols = data["configuration"]["columns"];
    std::cout << "[NXLoader] Opened " << path << " - "
                << " rows: " << design_rows << ", "
                << " columns: " << design_cols
                << std::endl;
    assert(
        (design_rows == model->get_rows()   ) &&
        (design_cols == model->get_columns())
    );
    // Load up all of the instructions and output mappings
    for (const auto & node : data["nodes"]) {
        uint32_t row    = node["row"];
        uint32_t column = node["column"];
        // Load instructions
        for (const auto & json_instr : node["instructions"]) {
            uint64_t instr = json_instr;
            std::cout << "[NXLoader] Loading row: " << row
                        << " column: " << column << " instruction: 0x"
                        << std::hex << instr << std::dec << std::endl;
            node_load_instr_t msg;
            msg.header.row     = row;
            msg.header.column  = column;
            msg.header.command = NODE_COMMAND_LOAD_INSTR;
            msg.instr          = NXConstants::unpack_instruction((uint8_t *)&instr);
            model->get_mesh()->m_ingress->enqueue(msg);
        }
        // Load output mappings
        uint32_t output_index = 0;
        for (const auto & outputs : node["messages"]) {
            // Convert all of the mappings
            for (const auto & mappings : outputs) {
                node_map_output_t msg;
                msg.header.row     = row;
                msg.header.column  = column;
                msg.header.command = NODE_COMMAND_MAP_OUTPUT;
                msg.source_index   = output_index;
                msg.target_row     = mappings[0];
                msg.target_column  = mappings[1];
                msg.target_index   = mappings[2];
                msg.target_is_seq  = mappings[3];
                std::cout << "[NXLoader] Loading row: " << row
                            << " column: " << column
                            << " SI: " << std::dec << (int)output_index
                            << " TR: " << std::dec << (int)msg.target_row
                            << " TC: " << std::dec << (int)msg.target_column
                            << " TI: " << std::dec << (int)msg.target_index
                            << " TS: " << std::dec << (int)msg.target_is_seq << std::endl;
                model->get_mesh()->m_ingress->enqueue(msg);
            }
            // Move to the next output
            output_index += 1;
        }
    }
    // Run the mesh until it sinks all of the queued messages
    uint32_t steps = 0;
    while (!model->get_mesh()->is_idle()) {
        model->get_mesh()->step(false);
        steps++;
    }
    std::cout << "[NXLoader] Ran mesh for " << steps << " steps" << std::endl;
}
