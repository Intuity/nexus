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
#include <iostream>
#include <optional>
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

#include "nxmodule.hpp"

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

    void resolveExpression(const Expression & expr) {
        switch (expr.kind) {
            case ExpressionKind::Assignment: {
                auto & asgn = expr.as<AssignmentExpression>();
                if (!asgn.isNonBlocking()) std::cout << "assign ";
                resolveExpression(asgn.left());
                std::cout << (asgn.isNonBlocking() ? " <= " : " = ");
                resolveExpression(asgn.right());
                std::cout << ";";
                break;
            }

            case ExpressionKind::NamedValue: {
                auto & nval = expr.as<NamedValueExpression>();

                switch (nval.symbol.kind) {
                    // Handles 'wire'
                    case SymbolKind::Net: {
                        auto & sym = nval.symbol.as<NetSymbol>();
                        std::cout << sym.name;
                        break;
                    }
                    // Handles 'reg'
                    case SymbolKind::Variable: {
                        auto & sym = nval.symbol.as<VariableSymbol>();
                        std::cout << sym.name;
                        break;
                    }
                    default: {
                        std::cout << "<UNSUPPORTED SYM: "
                                  << toString(nval.symbol.kind) << ">";
                        break;
                    }
                }

                break;
            }

            case ExpressionKind::IntegerLiteral: {
                const auto & itl = expr.as<IntegerLiteral>().getValue();
                std::optional<unsigned int> uint_val = itl.as<unsigned int>();
                std::cout << std::dec << uint_val.value_or(0);
                break;
            }

            case ExpressionKind::ElementSelect: {
                auto & val = expr.as<ElementSelectExpression>().value();
                auto & sel = expr.as<ElementSelectExpression>().selector();

                resolveExpression(val);
                std::cout << "[";
                resolveExpression(sel);
                std::cout << "]";

                break;
            }

            case ExpressionKind::RangeSelect: {
                auto & value = expr.as<RangeSelectExpression>().value();
                auto & left  = expr.as<RangeSelectExpression>().left();
                auto & right = expr.as<RangeSelectExpression>().right();
                resolveExpression(value);
                std::cout << "[";
                resolveExpression(left);
                std::cout << ":";
                resolveExpression(right);
                std::cout << "]";
                break;
            }

            case ExpressionKind::Concatenation: {
                std::cout << "{ ";
                bool first = true;
                for (auto * elem : expr.as<ConcatenationExpression>().operands()) {
                    if (!first) std::cout << ", ";
                    resolveExpression(*elem);
                    first = false;
                }
                std::cout << " }";
                break;
            }

            case ExpressionKind::Conversion: {
                resolveExpression(expr.as<ConversionExpression>().operand());
                break;
            }

            case ExpressionKind::UnaryOp: {
                UnaryOperator op = expr.as<UnaryExpression>().op;
                auto & value     = expr.as<UnaryExpression>().operand();
                std::cout << toString(op) << "(";
                resolveExpression(value);
                std::cout << ")";
                break;
            }

            case ExpressionKind::BinaryOp: {
                BinaryOperator op = expr.as<BinaryExpression>().op;
                auto & left       = expr.as<BinaryExpression>().left();
                auto & right      = expr.as<BinaryExpression>().left();
                std::cout << toString(op) << "(";
                resolveExpression(left);
                std::cout << ", ";
                resolveExpression(right);
                std::cout << ")";
                break;
            }

            case ExpressionKind::ConditionalOp: {
                auto & pred  = expr.as<ConditionalExpression>().pred();
                auto & left  = expr.as<ConditionalExpression>().left();
                auto & right = expr.as<ConditionalExpression>().right();
                std::cout << "(";
                resolveExpression(pred);
                std::cout << " ? ";
                resolveExpression(left);
                std::cout << " : ";
                resolveExpression(right);
                std::cout << ")";
                break;
            }

            default: {
                std::cout << "<UNSUPPORTED EXPR: " << toString(expr.kind) << ">";
                assert(!"Hit unsupported expression");
                break;
            }
        }
    }

    // Handle continuous assignments (e.g. `assign a = b & c`)
    void handle (const ContinuousAssignSymbol & symbol) {
        std::cout << " + ";
        auto & asgn = symbol.getAssignment();
        resolveExpression(asgn);
        std::cout << std::endl;
        visitDefault(symbol);
    }

    void resolveTimingControl (const TimingControl & ctrl) {
        switch (ctrl.kind) {

            case TimingControlKind::EventList: {
                bool first = true;
                for (const auto * event : ctrl.as<EventListControl>().events) {
                    if (!first) std::cout << ", ";
                    resolveTimingControl(*event);
                    first = false;
                }
                break;
            }

            case TimingControlKind::SignalEvent: {
                EdgeKind     edge = ctrl.as<SignalEventControl>().edge;
                const auto & expr = ctrl.as<SignalEventControl>().expr;
                std::cout << toString(edge) << " ";
                resolveExpression(expr);
                break;
            }

            default: {
                std::cout << "<UNSUPPORTED CTRL: " << toString(ctrl.kind) << ">";
                assert(!"Hit unsupported timing control");
                break;
            }

        }
    }

    void resolveStatement (const Statement & stmt) {
        switch (stmt.kind) {

            case StatementKind::Timed: {
                std::cout << "@(";
                resolveTimingControl(stmt.as<TimedStatement>().timing);
                std::cout << ") ";
                resolveStatement(stmt.as<TimedStatement>().stmt);
                break;
            }

            case StatementKind::Conditional: {
                std::cout << "if (";
                resolveExpression(stmt.as<ConditionalStatement>().cond);
                std::cout << ") ";
                resolveStatement(stmt.as<ConditionalStatement>().ifTrue);
                std::cout << " else ";
                resolveStatement(*(stmt.as<ConditionalStatement>().ifFalse));
                break;
            }

            case StatementKind::ExpressionStatement: {
                resolveExpression(stmt.as<ExpressionStatement>().expr);
                break;
            }

            default: {
                std::cout << "<UNSUPPORTED STMT: " << toString(stmt.kind) << ">";
                assert(!"Hit unsupported statement");
                break;
            }

        }
    }

    // Handle procedural blocks (e.g. always/always_ff/always_comb)
    void handle (const ProceduralBlockSymbol & symbol) {
        std::cout << " + ";

        switch (symbol.procedureKind) {
            case ProceduralBlockKind::Always: {
                std::cout << "always ";
                resolveStatement(symbol.getBody());
                break;
            }
            default: {
                std::cout << "<UNSUPPORTED PROC: " << toString(symbol.procedureKind) << ">";
                assert(!"Hit unsupported procedural block");
                break;
            }
        }

        std::cout << std::endl;

        visitDefault(symbol);
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
