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

#include <list>

#include <slang/types/AllTypes.h>
#include <slang/symbols/ASTVisitor.h>
#include <slang/compilation/Compilation.h>
#include <slang/compilation/SemanticModel.h>
#include <slang/syntax/SyntaxTree.h>
#include <slang/syntax/SyntaxPrinter.h>
#include <slang/syntax/SyntaxVisitor.h>

#include "nxmodule.hpp"

namespace Nexus {

    using namespace slang;

    class NXBitHolder
    {
    public:

        void append ( std::shared_ptr<NXSignal> bit )
        {
            m_bits.push_back(bit);
        }

        unsigned int total_width ( void )
        {
            return m_bits.size();
        }

        std::vector< std::shared_ptr<NXSignal> > m_bits;
    };

    class NXParser : public ASTVisitor<NXParser, true, true>
    {
    public:

        // Constructor
        NXParser ( )
            : ASTVisitor<NXParser, true, true> (       )
            , m_module                         ( NULL  )
            , m_in_process                     ( false )
            , m_proc_clk                       ( NULL  )
            , m_proc_rst                       ( NULL  )
        { }

        // Handle module instances (e.g. `module my_module (...); ... endmodule`)
        void handle ( const InstanceSymbol & symbol );

        // Handle port declarations (e.g. `input logic [31:0] i_blah`)
        void handle ( const PortSymbol & symbol );

        // Handle storage variables (e.g. `reg [31:0] foo`)
        void handle ( const VariableSymbol & symbol );

        // Handle net declarations (e.g. `wire [31:0] foo`)
        void handle ( const NetSymbol & symbol );

        void resolveExpression(const Expression & expr);

        // Handle continuous assignments (e.g. `assign a = b & c`)
        void handle ( const ContinuousAssignSymbol & symbol );

        void resolveTimingControl ( const TimingControl & ctrl );

        void resolveStatement ( const Statement & stmt );

        // Handle procedural blocks (e.g. always/always_ff/always_comb)
        void handle ( const ProceduralBlockSymbol & symbol );

        // Total width of accumulated operands
        unsigned int operand_width ( void )
        {
            unsigned int width = 0;
            for (auto holder : m_operands) width += holder->total_width();
            return width;
        }

    private:

        typedef std::shared_ptr<NXSignal> NXSignalPtr;
        typedef std::list< NXSignalPtr > NXSignalList;

        std::shared_ptr<NXModule>                 m_module;
        std::map< std::string, NXSignalList >     m_expansions;
        std::list< std::shared_ptr<NXBitHolder> > m_operands;
        bool                                      m_in_process;
        NXSignalList                              m_pos_trig;
        NXSignalList                              m_neg_trig;
        NXSignalPtr                               m_proc_clk;
        NXSignalPtr                               m_proc_rst;
        std::map< std::string, NXSignalPtr >      m_proc_asgn;

    };

}
