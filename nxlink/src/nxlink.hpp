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

#ifndef __NX_LINK_HPP__
#define __NX_LINK_HPP__

namespace NXLink {

    typedef struct {
        unsigned int major;
        unsigned int minor;
    } nx_version_t;

    typedef struct {
        unsigned int counter_width;
        unsigned int rows;
        unsigned int columns;
        unsigned int node_inputs;
        unsigned int node_outputs;
        unsigned int node_registers;
    } nx_parameters_t;

}

#endif // __NX_LINK_HPP__