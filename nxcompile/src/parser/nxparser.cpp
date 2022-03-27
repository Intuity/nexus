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

#include <algorithm>
#include <iostream>
#include <plog/Log.h>

#include "nxparser.hpp"
#include "nxconstant.hpp"

using namespace Nexus;
using namespace slang;

// Handle module instances (e.g. `module my_module (...); ... endmodule`)
void NXParser::handle (const InstanceSymbol & symbol) {
    std::cout << "INSTANCE: " << symbol.name << std::endl;
    m_module = std::make_shared<NXModule>(static_cast<std::string>(symbol.name));
    visitDefault(symbol);
}

// Handle port declarations (e.g. `input logic [31:0] i_blah`)
void NXParser::handle (const PortSymbol & symbol) {
    std::string sig_name = static_cast<std::string>(symbol.name);
    if (symbol.getType().isScalar()) {
        // 1-bit wide signals
        ScalarType * s_type = (ScalarType *)&symbol.getType();
        // TODO: This should also create a flop if output is registered
        if (!m_module->has_signal(sig_name)) {
            switch (symbol.direction) {
                case ArgumentDirection::In: {
                    auto port = std::make_shared<NXPortIn>(sig_name);
                    m_module->add_port(port);
                    m_expansions[sig_name] = NXSignalList({port});
                    break;
                }
                case ArgumentDirection::Out: {
                    auto port = std::make_shared<NXPortOut>(sig_name);
                    m_module->add_port(port);
                    m_expansions[sig_name] = NXSignalList({port});
                    break;
                }
                default:
                    PLOGE << "Port '" << sig_name << "' has bad direction "
                          << toString(symbol.direction);
                    assert(!"Bad direction");
                    break;
            }
        }
    } else if (symbol.getType().isPackedArray()) {
        // Multi-bit wide signals
        PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
        if (p_type->elementType.isScalar()) {
            ScalarType * s_elem = (ScalarType *)&p_type->elementType;
            int32_t rng_hi = p_type->range.upper();
            int32_t rng_lo = p_type->range.lower();
            if (m_expansions.find(sig_name) == m_expansions.end()) {
                m_expansions[sig_name] = NXSignalList();
            }
            for (int idx = rng_lo; idx <= rng_hi; idx++) {
                std::stringstream port_name;
                port_name << sig_name << "_" << std::dec << idx;
                if (!m_module->has_signal(port_name.str())) {
                    switch (symbol.direction) {
                        case ArgumentDirection::In: {
                            auto port = std::make_shared<NXPortIn>(port_name.str());
                            m_module->add_port(port);
                            m_expansions[sig_name].push_back(port);
                            break;
                        }
                        case ArgumentDirection::Out: {
                            auto port = std::make_shared<NXPortOut>(port_name.str());
                            m_module->add_port(port);
                            m_expansions[sig_name].push_back(port);
                            break;
                        }
                        default:
                            PLOGE << "Port '" << port_name.str()
                                << "' has unsupported direction "
                                << toString(symbol.direction);
                            assert(!"Bad direction");
                            break;
                    }
                }
            }
        } else {
            PLOGE << "PACKED ARRAY OF UNKNOWN TYPE";
            assert(!"Bad packed array");
        }
    } else {
        // Other types
        PLOGE << "TYPE UNKNOWN";
        assert(!"Bad type");
    }
    visitDefault(symbol);
}

// Handle storage variables (e.g. `reg [31:0] foo`)
void NXParser::handle (const VariableSymbol & symbol) {
    std::string sig_name = static_cast<std::string>(symbol.name);
    if (symbol.getType().isScalar()) {
        if (!m_module->has_signal(sig_name)) {
            auto flop = std::make_shared<NXFlop>(sig_name);
            m_module->add_flop(flop);
            m_expansions[sig_name] = NXSignalList({flop});
        }
    } else if (symbol.getType().isPackedArray()) {
        // Multi-bit wide signals
        PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
        if (p_type->elementType.isScalar()) {
            ScalarType * s_elem = (ScalarType *)&p_type->elementType;
            int32_t rng_hi = p_type->range.upper();
            int32_t rng_lo = p_type->range.lower();
            if (m_expansions.find(sig_name) == m_expansions.end()) {
                m_expansions[sig_name] = NXSignalList();
            }
            for (int idx = rng_lo; idx <= rng_hi; idx++) {
                std::stringstream flop_name;
                flop_name << sig_name << "_" << std::dec << idx;
                if (!m_module->has_signal(flop_name.str())) {
                    auto flop = std::make_shared<NXFlop>(flop_name.str());
                    m_module->add_flop(flop);
                    m_expansions[sig_name].push_back(flop);
                }
            }
        } else {
            PLOGE << " [PACKED ARRAY OF UNKNOWN TYPE]";
            assert(!"Bad packed array");
        }
    } else {
        // Other types
        PLOGE << "TYPE UNKNOWN";
        assert(!"Bad type");
    }
    visitDefault(symbol);
}

// Handle net declarations (e.g. `wire [31:0] foo`)
void NXParser::handle (const NetSymbol & symbol) {
    std::string sig_name = static_cast<std::string>(symbol.name);
    if (symbol.getType().isScalar()) {
        if (!m_module->has_signal(sig_name)) {
            auto wire = std::make_shared<NXSignal>(sig_name);
            m_module->add_wire(wire);
            m_expansions[sig_name] = NXSignalList({wire});
        }

    } else if (symbol.getType().isPackedArray()) {
        // Multi-bit wide signals
        PackedArrayType * p_type = (PackedArrayType *)&symbol.getType();
        if (p_type->elementType.isScalar()) {
            ScalarType * s_elem = (ScalarType *)&p_type->elementType;
            int32_t rng_hi = p_type->range.upper();
            int32_t rng_lo = p_type->range.lower();
            if (m_expansions.find(sig_name) == m_expansions.end()) {
                m_expansions[sig_name] = NXSignalList();
            }
            for (int idx = rng_lo; idx <= rng_hi; idx++) {
                std::stringstream wire_name;
                wire_name << sig_name << "_" << std::dec << idx;
                if (!m_module->has_signal(wire_name.str())) {
                    auto wire = std::make_shared<NXSignal>(wire_name.str());
                    m_module->add_wire(wire);
                    m_expansions[sig_name].push_back(wire);
                }
            }
        } else {
            PLOGE << "PACKED ARRAY OF UNKNOWN TYPE";
            assert(!"Bad packed array");
        }
    } else {
        // Other types
        PLOGE << "TYPE UNKNOWN";
        assert(!"Bad type");
    }
    visitDefault(symbol);
}

void NXParser::resolveExpression(const Expression & expr) {
    switch (expr.kind) {
        case ExpressionKind::Assignment: {
            // Get the first operand
            resolveExpression(expr.as<AssignmentExpression>().left());
            assert(m_operands.size() == 1);
            auto lhs = m_operands.front();
            m_operands.pop_front();

            // Get the second operand
            resolveExpression(expr.as<AssignmentExpression>().right());

            // Check total RHS operands are the same as LHS width
            assert(operand_width() == lhs->m_bits.size());

            unsigned int lhs_idx = 0;
            for (auto rh_holder : m_operands) {
                for (auto rhs : rh_holder->m_bits) {
                    // Inside a process, add entries to the map
                    if (m_in_process) {
                        m_proc_asgn[lhs->m_bits[lhs_idx]->m_name] = rhs;
                    // Outside a process, link from the previous term
                    } else {
                        rhs->add_output(lhs->m_bits[lhs_idx]);
                        lhs->m_bits[lhs_idx]->add_input(rhs);
                    }
                    lhs_idx++;
                }
            }

            // NOTE: Do not insert a result into the operands list, as
            //       assignments are a direct property of the block

            // Clear RHS operands
            m_operands.clear();

            break;
        }

        case ExpressionKind::NamedValue: {
            auto & nval = expr.as<NamedValueExpression>();

            auto holder = std::make_shared<NXBitHolder>();
            switch (nval.symbol.kind) {
                // Handles 'wire'
                case SymbolKind::Net: {
                    auto & sym = nval.symbol.as<NetSymbol>();
                    for (auto sig : m_expansions[static_cast<std::string>(sym.name)]) {
                        holder->append(sig);
                    }
                    break;
                }
                // Handles 'reg'
                case SymbolKind::Variable: {
                    auto & sym = nval.symbol.as<VariableSymbol>();
                    for (auto sig : m_expansions[static_cast<std::string>(sym.name)]) {
                        holder->append(sig);
                    }
                    break;
                }
                default: {
                    PLOGE << "UNSUPPORTED SYM: " << toString(nval.symbol.kind);
                    break;
                }
            }
            m_operands.push_back(holder);

            break;
        }

        case ExpressionKind::IntegerLiteral: {
            const auto & literal = expr.as<IntegerLiteral>().getValue();
            unsigned int value   = literal.as<unsigned int>().value_or(0);
            bitwidth_t   width   = literal.getBitWidth();

            auto holder = std::make_shared<NXBitHolder>();
            for (unsigned int idx = 0; idx < width; idx++) {
                holder->append(std::make_shared<NXConstant>(
                    (value >> idx) & 0x1, 1
                ));
            }
            m_operands.push_back(holder);

            break;
        }

        case ExpressionKind::ElementSelect: {
            auto & sig_expr = expr.as<ElementSelectExpression>().value();
            auto & sel_expr = expr.as<ElementSelectExpression>().selector();

            assert(sig_expr.kind == ExpressionKind::NamedValue);
            assert(sel_expr.kind == ExpressionKind::IntegerLiteral);

            const auto & sel_val = sel_expr.as<IntegerLiteral>().getValue();
            std::optional<unsigned int> sel_uint = sel_val.as<unsigned int>();

            std::stringstream lookup;
            lookup << sig_expr.as<NamedValueExpression>().symbol.name
                   << "_" << std::dec << sel_uint.value_or(0);

            auto holder = std::make_shared<NXBitHolder>();
            holder->append(m_module->get_signal(lookup.str()));

            m_operands.push_back(holder);

            break;
        }

        case ExpressionKind::RangeSelect: {
            auto & sig_expr   = expr.as<RangeSelectExpression>().value();
            auto & left_expr  = expr.as<RangeSelectExpression>().left();
            auto & right_expr = expr.as<RangeSelectExpression>().right();

            assert(sig_expr.kind   == ExpressionKind::NamedValue    );
            assert(left_expr.kind  == ExpressionKind::IntegerLiteral);
            assert(right_expr.kind == ExpressionKind::IntegerLiteral);

            const auto & left_val = left_expr.as<IntegerLiteral>().getValue();
            std::optional<unsigned int> left_uint = left_val.as<unsigned int>();

            const auto & right_val = right_expr.as<IntegerLiteral>().getValue();
            std::optional<unsigned int> right_uint = right_val.as<unsigned int>();

            unsigned int lower = std::min(left_uint.value_or(0), right_uint.value_or(0));
            unsigned int upper = std::max(left_uint.value_or(0), right_uint.value_or(0));

            auto holder = std::make_shared<NXBitHolder>();
            for (unsigned int idx = lower; idx <= upper; idx++) {
                std::stringstream lookup;
                lookup << sig_expr.as<NamedValueExpression>().symbol.name
                       << "_" << std::dec << idx;
                holder->append(m_module->get_signal(lookup.str()));
            }
            m_operands.push_back(holder);
            break;
        }

        case ExpressionKind::Concatenation: {
            // First resolve all of the consituent terms
            for (auto * elem : expr.as<ConcatenationExpression>().operands()) {
                resolveExpression(*elem);
            }

            // Build a new bit holder to join together the terms
            auto holder = std::make_shared<NXBitHolder>();
            for (auto operand : m_operands) {
                for (auto bit : operand->m_bits) {
                    holder->append(bit);
                }
            }

            // Replace the operands list
            m_operands.clear();
            m_operands.push_back(holder);
            break;
        }

        case ExpressionKind::Conversion: {
            resolveExpression(expr.as<ConversionExpression>().operand());
            break;
        }

        case ExpressionKind::UnaryOp: {
            // First resolve the operand
            resolveExpression(expr.as<UnaryExpression>().operand());

            // Map the operation to a gate type
            UnaryOperator       ast_op = expr.as<UnaryExpression>().op;
            NXGate::nxgate_op_t nx_op  = NXGate::UNKNOWN;
            bool                reduce = true;
            switch (ast_op) {
                case UnaryOperator::BitwiseNot:
                    reduce = false;
                    nx_op  = NXGate::NOT;
                    break;
                case UnaryOperator::LogicalNot:
                    nx_op = NXGate::NOT;
                    break;
                case UnaryOperator::BitwiseAnd:
                    nx_op = NXGate::AND;
                    break;
                case UnaryOperator::BitwiseOr:
                    nx_op = NXGate::OR;
                    break;
                case UnaryOperator::BitwiseXor:
                    nx_op = NXGate::XOR;
                    break;
                default:
                    PLOGE << "Unsupported unary operation " << toString(ast_op);
                    assert(!"Unsupported unary operation");
                    break;
            }

            // Check for only one input
            assert(m_operands.size() == 1);

            // Build the gate as either a reduction or bitwise (for invert)
            auto holder = std::make_shared<NXBitHolder>();
            auto inputs = m_operands.front();
            if (reduce) {
                auto gate = std::make_shared<NXGate>(nx_op);
                for (auto bit : inputs->m_bits) {
                    gate->add_input(bit);
                    bit->add_output(gate);
                }
                holder->append(gate);
                m_module->add_gate(gate);
            } else {
                for (auto bit : inputs->m_bits) {
                    auto gate = std::make_shared<NXGate>(nx_op);
                    gate->add_input(bit);
                    bit->add_output(gate);
                    holder->append(gate);
                    m_module->add_gate(gate);
                }
            }

            // Replace the operands list
            m_operands.clear();
            m_operands.push_back(holder);
            break;
        }

        case ExpressionKind::BinaryOp: {
            // Get the first operand
            resolveExpression(expr.as<BinaryExpression>().left());
            assert(m_operands.size() == 1);
            auto lhs = m_operands.front();
            m_operands.pop_front();

            // Get the second operand
            resolveExpression(expr.as<BinaryExpression>().right());
            assert(m_operands.size() == 1);
            auto rhs = m_operands.front();
            m_operands.pop_front();

            // Check bit counts match
            assert(lhs->m_bits.size() == rhs->m_bits.size());

            // Build the operation
            BinaryOperator      ast_op = expr.as<BinaryExpression>().op;
            NXGate::nxgate_op_t nx_op  = NXGate::UNKNOWN;
            switch (ast_op) {
                case BinaryOperator::BinaryAnd:
                    nx_op = NXGate::AND;
                    break;
                case BinaryOperator::BinaryOr:
                    nx_op = NXGate::OR;
                    break;
                case BinaryOperator::BinaryXor:
                    nx_op = NXGate::XOR;
                    break;
                default:
                    PLOGE << "Unsupported binary operation " << toString(ast_op);
                    assert(!"Unsupported binary operation");
                    break;
            }

            // Build a gate for each bit
            auto holder = std::make_shared<NXBitHolder>();
            for (unsigned int idx = 0; idx < lhs->m_bits.size(); idx++) {
                auto gate = std::make_shared<NXGate>(nx_op);
                gate->add_input(lhs->m_bits[idx]);
                gate->add_input(rhs->m_bits[idx]);
                lhs->m_bits[idx]->add_output(gate);
                rhs->m_bits[idx]->add_output(gate);
                holder->append(gate);
                m_module->add_gate(gate);
            }

            // Replace operands list
            m_operands.clear();
            m_operands.push_back(holder);
            break;
        }

        case ExpressionKind::ConditionalOp: {
            // Get the predicate
            resolveExpression(expr.as<ConditionalExpression>().pred());
            assert(m_operands.size() == 1);
            auto pred = m_operands.front();
            m_operands.pop_front();
            assert(pred->m_bits.size() == 1);

            // Get the first option
            resolveExpression(expr.as<ConditionalExpression>().left());
            assert(m_operands.size() == 1);
            auto lhs = m_operands.front();
            m_operands.pop_front();

            // Get the second option
            resolveExpression(expr.as<ConditionalExpression>().right());
            assert(m_operands.size() == 1);
            auto rhs = m_operands.front();
            m_operands.pop_front();

            // Check bit counts match
            assert(lhs->m_bits.size() == rhs->m_bits.size());

            // Build a gate for each bit
            auto holder = std::make_shared<NXBitHolder>();
            for (unsigned int idx = 0; idx < lhs->m_bits.size(); idx++) {
                auto gate = std::make_shared<NXGate>(NXGate::COND);
                gate->add_input(pred->m_bits[0]);
                gate->add_input(lhs->m_bits[idx]);
                gate->add_input(rhs->m_bits[idx]);
                pred->m_bits[0]->add_output(gate);
                lhs->m_bits[idx]->add_output(gate);
                rhs->m_bits[idx]->add_output(gate);
                holder->append(gate);
                m_module->add_gate(gate);
            }

            // Replace operands list
            m_operands.clear();
            m_operands.push_back(holder);
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
void NXParser::handle (const ContinuousAssignSymbol & symbol) {
    resolveExpression(symbol.getAssignment());
    visitDefault(symbol);
}

void NXParser::resolveTimingControl (const TimingControl & ctrl) {
    switch (ctrl.kind) {

        case TimingControlKind::EventList: {
            for (const auto * event : ctrl.as<EventListControl>().events)
                resolveTimingControl(*event);
            break;
        }

        case TimingControlKind::SignalEvent: {
            resolveExpression(ctrl.as<SignalEventControl>().expr);
            assert(m_operands.size() == 1);
            assert(m_operands.front()->m_bits.size() == 1);
            switch (ctrl.as<SignalEventControl>().edge) {
                case EdgeKind::PosEdge:
                    m_pos_trig.push_back(m_operands.front()->m_bits[0]);
                    break;
                case EdgeKind::NegEdge:
                    m_neg_trig.push_back(m_operands.front()->m_bits[0]);
                    break;
                default:
                    assert(!"Unsupported edge");
                    break;
            }
            m_operands.clear();
            break;
        }

        default: {
            std::cout << "<UNSUPPORTED CTRL: " << toString(ctrl.kind) << ">";
            assert(!"Hit unsupported timing control");
            break;
        }

    }
}

void NXParser::resolveStatement (const Statement & stmt) {
    switch (stmt.kind) {

        case StatementKind::Timed: {
            resolveTimingControl(stmt.as<TimedStatement>().timing);
            resolveStatement(stmt.as<TimedStatement>().stmt);
            break;
        }

        case StatementKind::Conditional: {
            // Get the conditional e.g. 'if (rst) ...'
            // NOTE: This is coded around the strict assumption of simple
            //       processes of the form - other forms may well break it
            //
            //          always @(posedge clk, posedge rst)
            //              if (rst) my_var_q <= 'd0;
            //              else     my_var_q <= my_var_d;
            //
            resolveExpression(stmt.as<ConditionalStatement>().cond);
            assert(m_operands.size() == 1);
            assert(m_operands.front()->m_bits.size() == 1);
            auto lcl_rst = m_operands.front()->m_bits[0];
            m_proc_clk   = NULL;
            m_proc_rst   = NULL;
            for (auto bit : m_pos_trig) {
                if (bit == lcl_rst) {
                    m_proc_rst = bit;
                } else {
                    assert(m_proc_clk == NULL);
                    m_proc_clk = bit;
                }
                if (m_proc_clk != NULL && m_proc_rst != NULL) break;
            }
            assert(m_proc_clk != NULL);
            assert(m_proc_rst != NULL);
            m_operands.clear();

            // Get assignments in the true section
            resolveStatement(stmt.as<ConditionalStatement>().ifTrue);
            std::map< std::string, std::shared_ptr<NXSignal> > all_true(m_proc_asgn);
            m_proc_asgn.clear();

            // Get assignments in the false section
            resolveStatement(*(stmt.as<ConditionalStatement>().ifFalse));
            std::map< std::string, std::shared_ptr<NXSignal> > all_false(m_proc_asgn);
            m_proc_asgn.clear();

            // Create flops for each case
            for (auto iter : all_true) {
                std::string sig_name = iter.first;
                auto        asgn_lhs = NXSignal::as<NXFlop>(m_module->get_signal(sig_name));
                auto        if_true  = iter.second;
                auto        if_false = all_false[sig_name];
                // PLOGI << "Flop - clk: " << m_proc_clk->m_name
                //            << ", rst: " << m_proc_rst->m_name
                //        << ", rst_val: " << if_true->m_name
                //              << ", D: " << if_false->m_name
                //              << ", Q: " << asgn_lhs->m_name;
                // Link up the flop to supporting signals
                asgn_lhs->m_clock   = m_proc_clk; // CLK
                asgn_lhs->m_reset   = m_proc_rst; // RST
                asgn_lhs->m_rst_val = if_true;    // RST_VAL
                asgn_lhs->add_input(if_false);    // D
                asgn_lhs->add_output(asgn_lhs);   // Q
                // Link supporting signals to the flop
                m_proc_clk->add_output(asgn_lhs);
                m_proc_rst->add_output(asgn_lhs);
                if_true->add_output(asgn_lhs);
                if_false->add_output(asgn_lhs);
            }
            break;
        }

        case StatementKind::ExpressionStatement: {
            resolveExpression(stmt.as<ExpressionStatement>().expr);
            break;
        }

        default: {
            PLOGE << "UNSUPPORTED STMT: " << toString(stmt.kind);
            assert(!"Hit unsupported statement");
            break;
        }

    }
}

// Handle procedural blocks (e.g. always/always_ff/always_comb)
void NXParser::handle (const ProceduralBlockSymbol & symbol) {
    // Guard against multiple entry
    assert(!m_in_process);
    m_in_process = true;

    // Detect the process type
    switch (symbol.procedureKind) {
        case ProceduralBlockKind::Always: {
            resolveStatement(symbol.getBody());
            break;
        }
        default: {
            PLOGE << "UNSUPPORTED PROC: " << toString(symbol.procedureKind);
            assert(!"Hit unsupported procedural block");
            break;
        }
    }

    // Handle the contents
    visitDefault(symbol);

    // Clear up
    m_in_process = false;
    m_pos_trig.clear();
    m_neg_trig.clear();
    m_proc_clk = NULL;
    m_proc_rst = NULL;
}