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
#include <slang/compilation/Compilation.h>
#include <slang/compilation/SemanticModel.h>
#include <slang/symbols/ASTVisitor.h>
#include <slang/syntax/SyntaxTree.h>
#include <slang/syntax/SyntaxPrinter.h>
#include <slang/syntax/SyntaxVisitor.h>
#include <slang/types/AllTypes.h>

#include "nxcompile.hpp"

using namespace slang;

class Visitor : public SyntaxVisitor<Visitor> {
public:

    Visitor () { }

    void visitToken(Token tkn) {

        std::cout << "VISITING: " << SyntaxPrinter().print(tkn).str() << std::endl;
    }

};

class VisitorAST : public ASTVisitor<VisitorAST, true, true>
{
public:

    // Handle module instances (e.g. `module my_module (...); ... endmodule`)
    void handle (const InstanceSymbol & symbol) {
        std::cout << "INSTANCE: " << symbol.name << std::endl;
        visitDefault(symbol);
    }

    // Handle port declarations (e.g. `input logic [31:0] i_blah`)
    void handle (const PortSymbol & symbol) {
        switch (symbol.direction) {
            case ArgumentDirection::In: std::cout << " - [IN ]"; break;
            case ArgumentDirection::Out: std::cout << " - [OUT]"; break;
            case ArgumentDirection::InOut: std::cout << " - [I/O]"; break;
            default: std::cout << " [??? "; break;
        }
        std::cout << " " << symbol.name;
        if (symbol.getType().isScalar()) {
            // 1-bit wide signals
            ScalarType * s_type = (ScalarType *)&symbol.getType();
            switch (s_type->scalarKind) {
                case ScalarType::Bit  : std::cout << " [BIT]";   break;
                case ScalarType::Logic: std::cout << " [LOGIC]"; break;
                case ScalarType::Reg  : std::cout << " [REG]";   break;
            }
            // std::cout << " W: " << std::dec << s_type->bitWidth << "]";
        } else if (symbol.getType().isPackedArray()) {
            // Multi-bit wide signals
            PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
            if (p_type->elementType.isScalar()) {
                ScalarType * s_elem = (ScalarType *)&p_type->elementType;
                switch (s_elem->scalarKind) {
                    case ScalarType::Bit  : std::cout << " [BIT";   break;
                    case ScalarType::Logic: std::cout << " [LOGIC"; break;
                    case ScalarType::Reg  : std::cout << " [REG";   break;
                }
                int32_t rng_hi = p_type->range.upper();
                int32_t rng_lo = p_type->range.lower();
                std::cout << " " << rng_hi << ":" << rng_lo << "]";
            } else {
                std::cout << " [PACKED ARRAY OF UNKNOWN TYPE]";
            }
        } else {
            // Other types
            std::cout << " [TYPE UNKNOWN]";
        }
        std::cout << std::endl;
        visitDefault(symbol);
    }

    // Handle storage variables (e.g. `reg [31:0] foo`)
    void handle (const VariableSymbol & symbol) {
        std::cout << " - " << symbol.name;
        ScalarType * s_type = (ScalarType *)&symbol.getType();
        if (symbol.getType().isScalar()) {
            switch (s_type->scalarKind) {
                case ScalarType::Bit  : std::cout << " [BIT]";   break;
                case ScalarType::Logic: std::cout << " [LOGIC]"; break;
                case ScalarType::Reg  : std::cout << " [REG]";   break;
            }
        } else if (symbol.getType().isPackedArray()) {
            // Multi-bit wide signals
            PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
            if (p_type->elementType.isScalar()) {
                ScalarType * s_elem = (ScalarType *)&p_type->elementType;
                switch (s_elem->scalarKind) {
                    case ScalarType::Bit  : std::cout << " [BIT";   break;
                    case ScalarType::Logic: std::cout << " [LOGIC"; break;
                    case ScalarType::Reg  : std::cout << " [REG";   break;
                }
                int32_t rng_hi = p_type->range.upper();
                int32_t rng_lo = p_type->range.lower();
                std::cout << " " << rng_hi << ":" << rng_lo << "]";
            } else {
                std::cout << " [PACKED ARRAY OF UNKNOWN TYPE]";
            }
        } else {
            // Other types
            std::cout << " [TYPE UNKNOWN]";
        }
        std::cout << std::endl;
        visitDefault(symbol);
    }

    // Handle net declarations (e.g. `wire [31:0] foo`)
    void handle (const NetSymbol & symbol) {
        std::cout << " - " << symbol.name;
        ScalarType * s_type = (ScalarType *)&symbol.getType();
        if (symbol.getType().isScalar()) {
            switch (s_type->scalarKind) {
                case ScalarType::Bit  : std::cout << " [BIT]";   break;
                case ScalarType::Logic: std::cout << " [LOGIC]"; break;
                case ScalarType::Reg  : std::cout << " [REG]";   break;
            }
        } else if (symbol.getType().isPackedArray()) {
            // Multi-bit wide signals
            PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
            if (p_type->elementType.isScalar()) {
                ScalarType * s_elem = (ScalarType *)&p_type->elementType;
                switch (s_elem->scalarKind) {
                    case ScalarType::Bit  : std::cout << " [BIT";   break;
                    case ScalarType::Logic: std::cout << " [LOGIC"; break;
                    case ScalarType::Reg  : std::cout << " [REG";   break;
                }
                int32_t rng_hi = p_type->range.upper();
                int32_t rng_lo = p_type->range.lower();
                std::cout << " " << rng_hi << ":" << rng_lo << "]";
            } else {
                std::cout << " [PACKED ARRAY OF UNKNOWN TYPE]";
            }
        } else {
            // Other types
            std::cout << " [TYPE UNKNOWN]";
        }
        std::cout << std::endl;
        visitDefault(symbol);
    }

    // Handle continuous assignments (e.g. `assign a = b & c`)
    void handle (const ContinuousAssignSymbol & symbol) {
        std::cout << " + assign ";
        AssignmentExpression * asgn = (AssignmentExpression *)&symbol.getAssignment();
        Expression             lhs  = asgn->left();
        switch (lhs.kind) {
            case ExpressionKind::NamedValue: {
                NamedValueExpression * expr = (NamedValueExpression *)&lhs;
                switch (expr->symbol.kind) {
                    case SymbolKind::Variable: {
                        std::cout << "<IS VARIABLE> " << expr->symbol.name;
                        break;
                    }
                    default: {
                        std::cout << "<UNKNOWN SYMBOL>";
                        break;
                    }
                }
                break;
            }
            default: {
                std::cout << "<UNSUPPORTED>";
                break;
            }
        }
        std::cout << " = ";
        Expression rhs = asgn->right();
        std::cout << ";" << std::endl;
    }

};

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
    auto options = parser.parse(argc, argv);

    // Detect if help was requested
    if (options.count("help")) {
        std::cout << parser.help() << std::endl;
        return 0;
    }

    auto & positional = options["positional"].as<std::vector<std::string>>();

    // Parse syntax tree with Slang
    auto tree = SyntaxTree::fromFile(positional[0]);

    Compilation compile;
    compile.addSyntaxTree(tree);

    VisitorAST ast;
    compile.getRoot().visit(ast);

    // Visitor visitor;
    // tree->root().visit(visitor);

    return 0;
}
