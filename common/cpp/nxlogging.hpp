// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

#ifndef __NXLOGGING_HPP__
#define __NXLOGGING_HPP__

#include <plog/Record.h>
#include <plog/Util.h>

namespace plog
{
    class NexusLogFormatter {
    public:
        static util::nstring header ();
        static util::nstring format ( const Record & record );
    };
}

namespace Nexus {

    void setup_logging ( bool verbose = false );

}

#endif // __NXLOGGING_HPP__
