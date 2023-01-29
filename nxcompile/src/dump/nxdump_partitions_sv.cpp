// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
#include <fstream>
#include <iostream>
#include <regex>

#include <plog/Log.h>

#include "nxconstant.hpp"
#include "nxdump_partitions_sv.hpp"

using namespace Nexus;

void Nexus::dump_partitions_to_sv ( std::shared_ptr<NXPartitioner> partitions, std::string out_path )
{
    PLOGI << "Dumping partitions of '" << partitions->m_module->m_name
          << "' to '" << out_path << "'";

    // Define lambda function to build safe names
    auto signame = [](std::shared_ptr<NXSignal> ptr) {
        if (ptr->m_type == NXSignal::CONSTANT)
            return "'d" + std::to_string(NXConstant::from_signal(ptr)->m_value);
        else
            return std::regex_replace(ptr->m_name, std::regex("\\."), "_");
    };

    // Open file handle
    std::ofstream fh;
    fh.open(out_path);

    // Write out the I/O boundary
    fh << "module " << partitions->m_module->m_name << " (" << std::endl;
    bool first = true;
    for (auto port : partitions->m_module->m_ports) {
        fh << (first ? "      " : "    , ");
        switch (port->m_port_type) {
            case NXPort::INPUT:
                fh << "input ";
                break;
            case NXPort::OUTPUT:
                fh << "output";
                break;
            default:
                assert(!"Unsupported port type");
        }
        fh << " logic " << signame(port) << std::endl;
        first = false;
    }
    fh << ");" << std::endl;

    // Declare all wires
    fh << "\n// Signals\n\n";
    for (auto gate : partitions->m_module->m_gates) {
        fh << "logic " << signame(gate) << ";" << std::endl;
    }

    // Walk through all partitions
    fh << "\n// Partitions\n\n";
    for (auto part : partitions->m_partitions) {
        fh << "// - Partition " << std::dec << part->m_index << std::endl;
        fh << "//   Flops" << std::endl;
        for (auto flop : part->m_flops) {
            fh << "logic " << signame(flop) << ";" << std::endl;
        }
        fh << std::endl;
        fh << "//   Processes" << std::endl;
        first = true;
        for (auto flop : part->m_flops) {
            if (!first) fh << std::endl;
            fh << "always @(posedge " << signame(flop->m_clock)
            <<        ", posedge " << signame(flop->m_reset) << ")" << std::endl;
            fh << "    if (" << signame(flop->m_reset) << ") "
            << signame(flop) << " <= " << signame(flop->m_rst_val) << ";" << std::endl;
            fh << "    else "
            << signame(flop) << " <= " << signame(NXPartition::chase_to_source(flop->m_inputs[0])) << ";" << std::endl;
            first = false;
        }
        fh << std::endl;
        fh << "//   Gates" << std::endl;
        for (auto gate : part->m_gates) {
            fh << "assign " << signame(gate) << " = ";
            // Basic assignment
            if (gate->m_op == NXGate::ASSIGN && gate->m_inputs.size() == 1) {
                fh << signame(NXPartition::chase_to_source(gate->m_inputs[0]));

            // Ternary expression: A ? B : C
            } else if (gate->m_op == NXGate::COND && gate->m_inputs.size() == 3) {
                fh << signame(NXPartition::chase_to_source(gate->m_inputs[0]))
                   << " ? " << signame(NXPartition::chase_to_source((gate->m_inputs[1])))
                   << " : " << signame(NXPartition::chase_to_source((gate->m_inputs[2])));

            // Binary & Unary Expressions
            } else if (
                gate->m_inputs.size() >= 1 &&
                (
                    (gate->m_op == NXGate::AND) ||
                    (gate->m_op == NXGate::OR ) ||
                    (gate->m_op == NXGate::NOT) ||
                    (gate->m_op == NXGate::XOR)
                )
            ) {
                // Determine the operation string
                std::string op_str;
                switch (gate->m_op) {
                    case NXGate::AND: op_str = "&"; break;
                    case NXGate::OR : op_str = "|"; break;
                    case NXGate::NOT: op_str = "!"; break;
                    case NXGate::XOR: op_str = "^"; break;
                    default: assert(!"Unsupported operation");
                }

                // Unary operations
                if (gate->m_inputs.size() == 1) {
                    fh << op_str << "(" << signame(NXPartition::chase_to_source(gate->m_inputs[0])) << ")";
                // Binary operations
                } else {
                    bool op_first = true;
                    for (auto input : gate->m_inputs) {
                        fh << (op_first ? "" : (" " + op_str + " ")) << signame(NXPartition::chase_to_source(input));
                        op_first = false;
                    }
                }

            // Unknown
            } else {
                assert(!"Unknown gate type");
            }
            fh << ";" << std::endl;
        }
        fh << std::endl;
    }

    // Other assignments
    fh << "\n// Other Assignments\n\n";
    for (auto wire : partitions->m_module->m_wires) {
        // Undriven signals
        if (wire->m_inputs.size() == 0) {
            fh << "assign " << signame(wire) << " = 'dX";

        // Gates - skip over as already handled by partitions
        } else if (wire->m_inputs.size() == 1 && wire->m_inputs[0]->m_type == NXSignal::GATE) {
            continue;

        // Basic assignments
        } else if (wire->m_inputs.size() == 1) {
            fh << "assign " << signame(wire) << " = " << signame(NXPartition::chase_to_source(wire->m_inputs[0]));

        // Unsupported number of drivers for one signal
        } else {
            assert(!"Unsupported number of inputs for a wire");

        }
        fh << ";" << std::endl;
    }

    // Drive outputs
    fh << "\n// Drive Outputs\n\n";
    for (auto port : partitions->m_module->m_ports) {
        // Skip non-output ports
        if (port->m_port_type != NXPort::OUTPUT) continue;
        // Check for a single driver
        assert(port->m_inputs.size() == 1);
        // Generate an assignment
        fh << "assign " << signame(port) << " = " << signame(port->m_inputs[0]) << ";" << std::endl;
    }

    // Write out end of module
    fh << std::endl << "endmodule : " << partitions->m_module->m_name << std::endl;

    // Close file
    fh.close();
}
