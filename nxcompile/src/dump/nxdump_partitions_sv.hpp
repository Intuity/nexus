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

#include <memory>
#include <string>

#include "nxpartitioner.hpp"

#ifndef __NXDUMP_PARTITIONS_SV_HPP__
#define __NXDUMP_PARTITIONS_SV_HPP__

namespace Nexus {

    void dump_partitions_to_sv ( std::shared_ptr<NXPartitioner> partitions, std::string out_path );

}

#endif // __NXDUMP_PARTITIONS_SV_HPP__
