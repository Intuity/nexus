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
#include <plog/Log.h>
#include <plog/Init.h>
#include <plog/Formatters/TxtFormatter.h>
#include <plog/Appenders/ColorConsoleAppender.h>
#include <slang/compilation/Compilation.h>
#include <slang/syntax/SyntaxTree.h>

#include "nxparser.hpp"

int main (int argc, const char ** argv) {
    // Initialize logging
    static plog::ColorConsoleAppender<plog::TxtFormatter> console;
    plog::init(plog::debug, &console);

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
        return 1;
    }

    // If help not requested, print standard welcome
    PLOGI << "NXCompile: Compiler for Nexus hardware";

    if (options.count("positional") == 0) {
        PLOGE << "No input files were specified";
        return 1;
    }

    auto & positional = options["positional"].as<std::vector<std::string>>();

    // Parse syntax tree with Slang
    auto tree = slang::SyntaxTree::fromFile(positional[0]);

    slang::Compilation compile;
    compile.addSyntaxTree(tree);

    Nexus::NXParser ast;
    compile.getRoot().visit(ast);

    return 0;
}
