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
#include <fstream>
#include <iostream>
#include <regex>

#include <plog/Log.h>

#include "nxconstant.hpp"
#include "nxdump_sv.hpp"

using namespace Nexus;

void Nexus::dump_to_sv ( std::shared_ptr<NXModule> module, std::string out_path )
{
    PLOGI << "Dumping '" << module->m_name << "' to '" << out_path << "'";

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
    fh << "module " << module->m_name << " (" << std::endl;
    bool first = true;
    for (auto port : module->m_ports) {
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
    fh << "\n// Wires\n\n";
    for (auto wire : module->m_wires) {
        fh << "logic " << signame(wire) << ";" << std::endl;
    }

    // Declare all flops
    fh << "\n// Flops\n\n";
    for (auto flop : module->m_flops) {
        fh << "logic " << signame(flop) << ";" << std::endl;
    }

    // Declare all processes
    fh << "\n// Processes\n\n";
    first = true;
    for (auto flop : module->m_flops) {
        if (!first) fh << std::endl;
        fh << "always @(posedge " << signame(flop->m_clock)
           <<        ", posedge " << signame(flop->m_reset) << ")" << std::endl;
        fh << "    if (" << signame(flop->m_reset) << ") "
           << signame(flop) << " <= " << signame(flop->m_rst_val) << ";" << std::endl;
        fh << "    else "
           << signame(flop) << " <= " << signame(flop->m_inputs[0]) << ";" << std::endl;
        first = false;
    }

    // Declare all gates
    fh << "\n// Gates and Assignments\n\n";
    for (auto wire : module->m_wires) {
        fh << "assign " << signame(wire) << " = ";
        // Undriven signals
        if (wire->m_inputs.size() == 0) {
            fh << "'dX";

        // Gates
        } else if (wire->m_inputs.size() == 1 && wire->m_inputs[0]->m_type == NXSignal::GATE) {
            auto gate = NXGate::from_signal(wire->m_inputs[0]);
            // Basic assignment
            if (gate->m_op == NXGate::ASSIGN && gate->m_inputs.size() == 1) {
                fh << signame(gate->m_inputs[0]);

            // Ternary expression: A ? B : C
            } else if (gate->m_op == NXGate::COND && gate->m_inputs.size() == 3) {
                fh << signame(gate->m_inputs[0])
                   << " ? " << signame(gate->m_inputs[1])
                   << " : " << signame(gate->m_inputs[2]);

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
                    fh << op_str << "(" << signame(gate->m_inputs[0]) << ")";
                // Binary operations
                } else {
                    bool op_first = true;
                    for (auto input : gate->m_inputs) {
                        fh << (op_first ? "" : (" " + op_str + " ")) << signame(input);
                        op_first = false;
                    }
                }

            // Unknown
            } else {
                assert(!"Unknown gate type");
            }

        // Basic assignments
        } else if (wire->m_inputs.size() == 1) {
            fh << signame(wire->m_inputs[0]);

        // Unsupported number of drivers for one signal
        } else {
            assert(!"Unsupported number of inputs for a wire");
        }
        fh << ";" << std::endl;
    }

    // Drive outputs
    fh << "\n// Drive Outputs\n\n";
    for (auto port : module->m_ports) {
        // Skip non-output ports
        if (port->m_port_type != NXPort::OUTPUT) continue;
        // Check for a single driver
        assert(port->m_inputs.size() == 1);
        // Generate an assignment
        fh << "assign " << signame(port) << " = " << signame(port->m_inputs[0]) << ";" << std::endl;
    }

    // Write out end of module
    fh << std::endl << "endmodule : " << module->m_name << std::endl;

    // Close file
    fh.close();
}
