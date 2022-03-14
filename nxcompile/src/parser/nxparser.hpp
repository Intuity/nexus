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

        void append ( std::shared_ptr<NXSignal> bit ) { m_bits.push_back(bit); }

        std::vector< std::shared_ptr<NXSignal> > m_bits;
    };

    class NXParser : public ASTVisitor<NXParser, true, true>
    {
    public:

        // Constructor
        NXParser ( )
            : ASTVisitor<NXParser, true, true> (      )
            , m_module                         ( NULL )
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

    private:

        std::shared_ptr<NXModule>                 m_module;
        std::list< std::shared_ptr<NXBitHolder> > m_operands;

    };

}
