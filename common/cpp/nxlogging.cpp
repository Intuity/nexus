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

#include <plog/Log.h>
#include <plog/Init.h>
#include <plog/Formatters/TxtFormatter.h>
#include <plog/Appenders/ColorConsoleAppender.h>

#include "nxlogging.hpp"

using namespace plog;

util::nstring plog::NexusLogFormatter::header ()
{
    return util::nstring();
}

util::nstring plog::NexusLogFormatter::format ( const Record & record )
{
    tm t;
    util::localtime_s(&t, &record.getTime().time);

    util::nostringstream ss;
    ss << (t.tm_year + 1900) << "-"
       << std::setfill(PLOG_NSTR('0')) << std::setw(2) << t.tm_mon + 1 << PLOG_NSTR("-")
       << std::setfill(PLOG_NSTR('0')) << std::setw(2) << t.tm_mday << PLOG_NSTR(" ");
    ss << std::setfill(PLOG_NSTR('0')) << std::setw(2) << t.tm_hour << PLOG_NSTR(":")
       << std::setfill(PLOG_NSTR('0')) << std::setw(2) << t.tm_min << PLOG_NSTR(":")
       << std::setfill(PLOG_NSTR('0')) << std::setw(2) << t.tm_sec << PLOG_NSTR(" ");
    ss << PLOG_NSTR("[") << severityToString(record.getSeverity()) << PLOG_NSTR("] ");
    ss << record.getMessage() << PLOG_NSTR("\n");

    return ss.str();
}


void Nexus::setup_logging ( bool verbose /* = false */ )
{
    static ColorConsoleAppender<NexusLogFormatter> console;
    init(info, &console);
    if (verbose) plog::get()->setMaxSeverity(plog::debug);
}
