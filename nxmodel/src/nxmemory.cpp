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

#include "nxmemory.hpp"

using namespace NXModel;

void NXMemory::clear ( void )
{
    m_contents.clear();
}

void NXMemory::write ( uint32_t address, uint32_t data, uint32_t mask )
{
    m_contents[address] = (
        ((read(address, 0)) & ~mask) |
        ((data            ) &  mask)
    );
}

uint32_t NXMemory::read ( uint32_t address, uint32_t def_value )
{
    return populated(address) ? m_contents[address] : def_value;
}

bool NXMemory::populated ( uint32_t address )
{
    return m_contents.find(address) != m_contents.end();
}
