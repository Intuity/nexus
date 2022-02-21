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
#include <string>
#include <vector>

#include <cxxopts.hpp>
#include <surelog/surelog.h>
#include <uhdm/ElaboratorListener.h>
#include <uhdm/uhdm.h>
#include <uhdm/vpi_listener.h>
#include <uhdm/vpi_visitor.h>

#include "nxcompile.hpp"

#define get_vpi_str(name, obj, typ) \
    std::string name; \
    { \
        const char * c_str = vpi_get_str(typ, obj); \
        name = c_str ? c_str : "N/A"; \
    }

std::string lookup_operation (unsigned int op_code)
{
    std::string op_str;
    switch (op_code) {
        case vpiMinusOp      : { op_str = "-";           break; }
        case vpiPlusOp       : { op_str = "+";           break; }
        case vpiNotOp        : { op_str = "!";           break; }
        case vpiBitNegOp     : { op_str = "~";           break; }
        case vpiUnaryAndOp   : { op_str = "&";           break; }
        case vpiUnaryNandOp  : { op_str = "!&";          break; }
        case vpiUnaryOrOp    : { op_str = "|";           break; }
        case vpiUnaryNorOp   : { op_str = "!|";          break; }
        case vpiUnaryXorOp   : { op_str = "^";           break; }
        case vpiUnaryXNorOp  : { op_str = "!^";          break; }
        case vpiSubOp        : { op_str = "-";           break; }
        case vpiDivOp        : { op_str = "/";           break; }
        case vpiModOp        : { op_str = "%";           break; }
        case vpiEqOp         : { op_str = "==";          break; }
        case vpiNeqOp        : { op_str = "!=";          break; }
        case vpiCaseEqOp     : { op_str = "==";          break; }
        case vpiCaseNeqOp    : { op_str = "!=";          break; }
        case vpiGtOp         : { op_str = ">";           break; }
        case vpiGeOp         : { op_str = ">=";          break; }
        case vpiLtOp         : { op_str = "<";           break; }
        case vpiLeOp         : { op_str = "<=";          break; }
        case vpiLShiftOp     : { op_str = "<<";          break; }
        case vpiRShiftOp     : { op_str = ">>";          break; }
        case vpiAddOp        : { op_str = "+";           break; }
        case vpiMultOp       : { op_str = "*";           break; }
        case vpiLogAndOp     : { op_str = "&&";          break; }
        case vpiLogOrOp      : { op_str = "||";          break; }
        case vpiBitAndOp     : { op_str = "&";           break; }
        case vpiBitOrOp      : { op_str = "|";           break; }
        case vpiBitXorOp     : { op_str = "^";           break; }
        case vpiBitXNorOp    : { op_str = "!^";          break; }
        case vpiConditionOp  : { op_str = "?";           break; }
        case vpiConcatOp     : { op_str = "{...}";       break; }
        case vpiMultiConcatOp: { op_str = "{***}";       break; }
        case vpiEventOrOp    : { op_str = "or";          break; } // As in @(posedge clk or posedge rst)
        case vpiNullOp       : { assert(!"UNSUPPORTED"); break; }
        case vpiListOp       : { op_str = ",";           break; } // As in @(posedge clk, posedge rst)
        case vpiMinTypMaxOp  : { assert(!"UNSUPPORTED"); break; }
        case vpiPosedgeOp    : { op_str = "@posedge";    break; }
        case vpiNegedgeOp    : { op_str = "@negedge";    break; }
        case vpiArithLShiftOp: { op_str = "<<";          break; }
        case vpiArithRShiftOp: { op_str = ">>";          break; }
        case vpiPowerOp      : { op_str = "**";          break; }
        default: { assert(!"UNKNOWN"); break; }
    }
    return op_str;
}

std::string handle_expr (vpiHandle ref)
{
    std::stringstream ref_ss;
    int               ref_type = vpi_get(vpiType, ref);
    switch (ref_type) {
        // Constant
        case vpiConstant: {

            s_vpi_value value = {0};
            vpi_get_value(ref, &value);
            // TODO: Need to implement something like visit_value from vpi_visitor
            //       to always return an integer no matter the encoded type
            ref_ss << value.value.str;
            // std::cerr << UHDM::visit_designs({ref}) << std::endl;
            // assert(!"Debug");
            break;
        }
        // Object References
        case vpiRefObj: {
            vpiHandle act      = vpi_handle(vpiActual, ref);
            int       act_type = vpi_get(vpiType, act);
            switch (act_type) {
                case vpiNet: {
                    get_vpi_str(act_net, act, vpiName);
                    ref_ss << act_net;
                    // Look for a range
                    vpiHandle net_rng = vpi_handle(vpiRange, act);
                    if (net_rng != NULL) {
                        vpiHandle net_rng_l_ref = vpi_handle(vpiLeftRange, net_rng);
                        vpiHandle net_rng_r_ref = vpi_handle(vpiRightRange, net_rng);
                        s_vpi_value net_rng_l = { 0 };
                        s_vpi_value net_rng_r = { 0 };
                        vpi_get_value(net_rng_l_ref, &net_rng_l);
                        vpi_get_value(net_rng_r_ref, &net_rng_r);
                        ref_ss << "[" << net_rng_l.value.integer
                                << ":" << net_rng_r.value.integer << "]";
                    }
                    break;
                }
                default: {
                    ref_ss << "<UNKNOWN_REF(" << act_type << ")>";
                    std::cerr << "UNKNOWN ACT TYPE: " << act_type << std::endl;
                    std::cerr << UHDM::visit_designs({act}) << std::endl;
                    assert(!"Unknown type");
                    break;
                }
            }
            break;
        }
        // Bit Select
        case vpiBitSelect: {
            get_vpi_str(bit_net, ref, vpiName);
            vpiHandle bit_idx_ref = vpi_handle(vpiIndex, ref);
            s_vpi_value bit_idx;
            vpi_get_value(bit_idx_ref, &bit_idx);
            ref_ss << bit_net << "[" << bit_idx.value.integer << "]";
            break;
        }
        // Part Select
        case vpiPartSelect: {
            vpiHandle   parent     = vpi_handle(vpiParent,     ref);
            vpiHandle   parent_act = vpi_handle(vpiActual,     parent);
            vpiHandle   rng_l_ref  = vpi_handle(vpiLeftRange,  ref);
            vpiHandle   rng_r_ref  = vpi_handle(vpiRightRange, ref);
            s_vpi_value rng_l, rng_r;
            vpi_get_value(rng_l_ref, &rng_l);
            vpi_get_value(rng_r_ref, &rng_r);
            get_vpi_str(part_net, parent_act, vpiName);
            ref_ss << part_net << "[" << rng_l.value.integer
                               << ":" << rng_r.value.integer << "]";
            break;
        }
        // Operation
        case vpiOperation: {
            // TODO: Complete operation handling
            unsigned int op_type       = vpi_get(vpiOpType, ref);
            vpiHandle    operands_iter = vpi_iterate(vpiOperand, ref);
            ref_ss << lookup_operation(op_type) << "(";
            bool first = true;
            while (vpiHandle operand = vpi_scan(operands_iter)) {
                ref_ss << (first ? "" : ", ") << handle_expr(operand);
                first = false;
            }
            ref_ss << ")";
            break;
        }
        // Default
        default: {
            ref_ss << "<UNKNOWN(" << ref_type << ")>";
            std::cerr << "UNKNOWN REF TYPE: " << ref_type << std::endl;
            std::cerr << UHDM::visit_designs({ref}) << std::endl;
            assert(!"Unknown type");
            break;
        }
    }
    return ref_ss.str();
}

std::string handle_statement (vpiHandle ref)
{
    std::stringstream ref_ss;
    int               ref_type = vpi_get(vpiType, ref);
    switch (ref_type) {
        // Event Control
        case vpiEventControl: {
            ref_ss << handle_expr(vpi_handle(vpiCondition, ref))
                   << " begin\n"
                   << handle_statement(vpi_handle(vpiStmt, ref))
                   << "\nend";
            break;
        }
        // IF-ELSE Statment
        case vpiIfElse: {
            vpiHandle cond      = vpi_handle(vpiCondition, ref);
            vpiHandle stmt_if   = vpi_handle(vpiStmt,      ref);
            vpiHandle stmt_else = vpi_handle(vpiElseStmt,  ref);
            ref_ss << "if (" << handle_expr(cond) << ") {\n"
                   << handle_statement(stmt_if) << "\n} else {\n"
                   << handle_statement(stmt_else) << "\n}";
            break;
        }
        // Assignment
        case vpiAssignment: {
            ref_ss << handle_expr(vpi_handle(vpiLhs, ref)) << " <= "
                   << handle_expr(vpi_handle(vpiRhs, ref));
            break;
        }
        // Default
        default: {
            ref_ss << "<UNKNOWN(" << ref_type << ")>";
            std::cerr << "UNKNOWN STATEMENT: " << ref_type << std::endl;
            std::cerr << UHDM::visit_designs({ref}) << std::endl;
            assert(!"Unknown statement");
            break;
        }
    }
    return ref_ss.str();
}

std::string handle_process (vpiHandle ref)
{
    std::stringstream ref_ss;
    int               ref_type = vpi_get(vpiType, ref);
    switch (ref_type) {
        // always block
        case vpiAlways: {
            ref_ss << "always" << handle_statement(vpi_handle(vpiStmt, ref));
            break;
        }
        // Default
        default: {
            ref_ss << "<UNKNOWN(" << ref_type << ")>";
            std::cerr << "UNKNOWN PROCESS: " << ref_type << std::endl;
            std::cerr << UHDM::visit_designs({ref}) << std::endl;
            assert(!"Unknown type");
            break;
        }
    }
    return ref_ss.str();
}

int main (int argc, const char ** argv) {
    // Create instance of cxxopts
    cxxopts::Options parser("nxcompile", "Compiler targeting Nexus hardware");

    // Setup options
    parser.add_options()
        // Debug/verbosity
        ("v,verbose", "Enable verbose output")
        ("h,help",    "Print help and usage information");

    // Setup positional options
    parser.add_options()
        ("positional", "Arguments", cxxopts::value<std::vector<std::string>>());
    parser.parse_positional("positional");

    // Run the parser
    // auto options = parser.parse(argc, argv);

    // Detect if help was requested
    // if (options.count("help")) {
    //     std::cout << parser.help() << std::endl;
    //     return 0;
    // }

    // auto & positional = options["positional"].as<std::vector<std::string>>();

    // Setup Surelog for Verilog parsing
    SURELOG::SymbolTable       * sym = new SURELOG::SymbolTable();
    SURELOG::ErrorContainer    * err = new SURELOG::ErrorContainer(sym);
    SURELOG::CommandLineParser * cmd = new SURELOG::CommandLineParser(err, sym, false, false);

    // std::cout << "File: " << positional[0].c_str() << std::endl;

    // const char * cmd_argv[] = {
    //     "surelog", // Dummy argument to placate Surelog's parser
    //     positional[0].c_str()
    // };
    cmd->noPython();
    cmd->setParse(true);
    cmd->setwritePpOutput(true);
    cmd->setCompile(true);
    cmd->setElaborate(true);
    // cmd->setElabUhdm(true);
    assert(cmd->parseCommandLine(argc, argv));

    SURELOG::scompiler * compiler = SURELOG::start_compiler(cmd);
    vpiHandle            design   = SURELOG::get_uhdm_design(compiler);
    auto stats = err->getErrorStats();
    assert(!stats.nbFatal);
    assert(!stats.nbSyntax);
    assert(!stats.nbError);

    if (design && !vpi_get(vpiElaborated, design)) {
        UHDM::Serializer srlz;
        UHDM::ElaboratorListener * lstn = new UHDM::ElaboratorListener(&srlz, true);
        listen_designs({design}, lstn);
    }
    assert(vpi_get(vpiElaborated, design));

    // std::cout << UHDM::visit_designs({design}) << std::endl;

    std::cout << std::endl;
    std::cout << "======= UHDM =======" << std::endl;
    std::cout << std::endl;

    std::cout << "Modules    :" << std::endl;
    vpiHandle mod_iter = vpi_iterate(UHDM::uhdmtopModules, design);
    while (vpiHandle mod = vpi_scan(mod_iter)) {
        // Double-check this is a module
        assert(vpi_get(vpiType, mod) == vpiModule);

        get_vpi_str(def_name, mod, vpiDefName);
        get_vpi_str(obj_name, mod, vpiFullName);

        std::cout << " - Def: " << def_name << ", Obj: " << obj_name << std::endl;

        // Extract port definitions
        vpiHandle port_iter = vpi_iterate(vpiPort, mod);
        while (vpiHandle port = vpi_scan(port_iter)) {
            get_vpi_str(port_name, port, vpiName);
            std::string dirx;
            switch (vpi_get(vpiDirection, port)) {
                case vpiInput : dirx = "INPUT "; break;
                case vpiOutput: dirx = "OUTPUT"; break;
                case vpiInout : dirx = "INOUT "; break;
            }
            bool is_scalar = vpi_get(vpiScalar, port);
            bool is_vector = vpi_get(vpiVector, port);
            int  port_size = vpi_get(vpiSize,   port);
            vpiHandle bits_iter = vpi_iterate(vpiBit, port);
            int num_bits = 0;
            while (vpiHandle bit = vpi_scan(bits_iter))
                num_bits += 1;
            vpiHandle low_conn = vpi_handle(vpiLowConn, port    );
            vpiHandle vpi_act  = vpi_handle(vpiActual,  low_conn);
            vpiHandle rng_itr = vpi_iterate(vpiRange, vpi_act);
            s_vpi_value lvalue = { 0 };
            s_vpi_value rvalue = { 0 };
            while (vpiHandle rng = vpi_scan(rng_itr)) {
                vpiHandle lconst = vpi_handle(vpiLeftRange,  rng);
                vpiHandle rconst = vpi_handle(vpiRightRange, rng);
                vpi_get_value(lconst, &lvalue);
                vpi_get_value(rconst, &rvalue);
                break;
            }
            std::cout << "   + [" << dirx << "] "
                      << "[" << lvalue.value.integer
                      << ":" << rvalue.value.integer << "] "
                      << " Sr: " << (is_scalar ? "Y" : "N")
                      << " Vr: " << (is_vector ? "Y" : "N")
                      << " Sz: " << port_size << " "
                      << port_name << std::endl;
            // vpiHandle ref_obj = vpi_handle(vpiRefObj, port);
            // std::cout << UHDM::visit_designs({vpi_act}) << std::endl;
        }

        // Extract 'reg' definitions
        vpiHandle net_iter = vpi_iterate(vpiNet, mod);
        while (vpiHandle net = vpi_scan(net_iter)) {
            unsigned int net_type = vpi_get(vpiNetType, net);
            get_vpi_str(net_name, net, vpiName);
            switch (net_type) {
                // 0: No associated type - skip
                case 0: break;
                // Declaration of 'wire'
                case vpiWire: {
                    vpiHandle net_rng_iter = vpi_iterate(vpiRange, net);
                    while (vpiHandle net_rng = vpi_scan(net_rng_iter)) {
                        vpiHandle net_rng_l_ref = vpi_handle(vpiLeftRange, net_rng);
                        vpiHandle net_rng_r_ref = vpi_handle(vpiRightRange, net_rng);
                        s_vpi_value net_rng_l, net_rng_r;
                        vpi_get_value(net_rng_l_ref, &net_rng_l);
                        vpi_get_value(net_rng_r_ref, &net_rng_r);
                        std::cout << "wire ["
                                  << net_rng_l.value.integer
                                  << ":"
                                  << net_rng_r.value.integer
                                  << "] " << net_name << ";" << std::endl;
                    }
                    break;
                }
                // Declaration of 'reg'
                case vpiReg: {
                    vpiHandle net_rng_iter = vpi_iterate(vpiRange, net);
                    while (vpiHandle net_rng = vpi_scan(net_rng_iter)) {
                        vpiHandle net_rng_l_ref = vpi_handle(vpiLeftRange, net_rng);
                        vpiHandle net_rng_r_ref = vpi_handle(vpiRightRange, net_rng);
                        s_vpi_value net_rng_l, net_rng_r;
                        vpi_get_value(net_rng_l_ref, &net_rng_l);
                        vpi_get_value(net_rng_r_ref, &net_rng_r);
                        std::cout << "reg ["
                                  << net_rng_l.value.integer
                                  << ":"
                                  << net_rng_r.value.integer
                                  << "] " << net_name << ";" << std::endl;
                    }
                    break;
                }
                // Default
                default: {
                    std::cerr << "UNKNOWN NET: " << net_type << std::endl;
                    std::cerr << UHDM::visit_designs({net}) << std::endl;
                    assert(!"Unknown net");
                    break;
                }
            }
        }

        // Extract continuous assignments
        vpiHandle asgn_iter = vpi_iterate(vpiContAssign, mod);
        while (vpiHandle asgn = vpi_scan(asgn_iter)) {
            std::cout << "assign "
                      << handle_expr(vpi_handle(vpiLhs, asgn)) << " = "
                      << handle_expr(vpi_handle(vpiRhs, asgn)) << ";" << std::endl;
        }

        // Extract processes
        vpiHandle proc_iter = vpi_iterate(vpiProcess, mod);
        while (vpiHandle proc = vpi_scan(proc_iter)) {
            std::cout << handle_process(proc) << std::endl;
        }

    }

    return 0;
}
