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
#include "nxdump_partitions_sv.hpp"
#include "nxdump_stats.hpp"
#include "nxdump_sv.hpp"
#include "nxopt_propagate.hpp"
#include "nxopt_prune.hpp"
#include "nxpartitioner.hpp"

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
        ("h,help",    "Print help and usage information")
        // Dump different stages
        ("dump-parsed",     "Dump logic immediately after parsing",  cxxopts::value<std::string>())
        ("dump-pruned",     "Dump logic after pruning",              cxxopts::value<std::string>())
        ("dump-propagated", "Dump logic after constant propagation", cxxopts::value<std::string>())
        ("dump-partitions", "Dump logic after partitioning",         cxxopts::value<std::string>())
        // Mesh configuration
        ("rows",    "Rows in the mesh",    cxxopts::value<unsigned int>()->default_value("10"))
        ("columns", "Columns in the mesh", cxxopts::value<unsigned int>()->default_value("10"))
        // Node configuration
        ("node-inputs",  "Number of inputs to each node",    cxxopts::value<unsigned int>()->default_value("32"))
        ("node-outputs", "Number of outputs from each node", cxxopts::value<unsigned int>()->default_value("32"))
        ("node-working", "Working registers per node",       cxxopts::value<unsigned int>()->default_value("16"));

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
    PLOGI << "Starting to parse '" << positional[0] << "'";
    auto module = Nexus::NXParser::parse_from_file(positional[0]);
    PLOGI << "Parser returned top-level '" << module->m_name << "'";

    // Dump base statistics
    std::cout << Nexus::dump_rtl_stats(module);

    // If requested, dump out parsed output
    if (options.count("dump-parsed"))
        Nexus::dump_to_sv(module, options["dump-parsed"].as<std::string>());

    // Prune, and then possibly dump
    PLOGI << "Pruning top-level '" << module->m_name << "'";
    Nexus::optimise_prune(module);
    if (options.count("dump-pruned"))
        Nexus::dump_to_sv(module, options["dump-pruned"].as<std::string>());

    // Dump pruned statistics
    std::cout << Nexus::dump_rtl_stats(module);

    // Propagate constants, prune, and then possibly dump
    PLOGI << "Propagating constants in top-level '" << module->m_name << "'";
    Nexus::optimise_propagate(module);
    Nexus::optimise_prune(module);
    if (options.count("dump-propagated"))
        Nexus::dump_to_sv(module, options["dump-propagated"].as<std::string>());

    // Dump propagated statistics
    std::cout << Nexus::dump_rtl_stats(module);

    // Partition the design
    PLOGI << "Running the partitioner";
    unsigned int nd_inputs  = options["node-inputs" ].as<unsigned int>();
    unsigned int nd_outputs = options["node-outputs"].as<unsigned int>();
    auto part = std::make_shared<Nexus::NXPartitioner>(
        module, nd_inputs, nd_outputs
    );
    part->run();

    // If requested, dump out partitioner output
    if (options.count("dump-partitions"))
        Nexus::dump_partitions_to_sv(part, options["dump-partitions"].as<std::string>());

    return 0;
}
