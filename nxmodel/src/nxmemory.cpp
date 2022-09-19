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

#include <fstream>
#include <string>
#include <sstream>

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

void NXMemory::dump ( std::string path, unsigned int cycle )
{
    if (m_dump_fh == NULL) {
        m_dump_fh = new std::fstream(path, std::iostream::out);
        if (!m_dump_fh->is_open()) assert(!"Failed to open dump file");

        *m_dump_fh << "// Dumping " << std::dec << m_contents.size() << " rows" << std::endl;
        *m_dump_fh << std::endl;
    }

    *m_dump_fh << "// Cycle " << std::dec << cycle << std::endl;
    for (const auto & entry : m_contents) {
        uint32_t row  = entry.first;
        uint32_t data = entry.second;
        *m_dump_fh << std::setw(4) << std::setfill('0') << std::dec << (unsigned int)row;
        *m_dump_fh << " :";
        for (int offset = 24; offset >= 0; offset -= 8) {
            unsigned int chunk = (data >> offset) & 0xFF;
            *m_dump_fh << " " << std::bitset<8>(chunk);
        }
        *m_dump_fh << " (0x" << std::setw(8) << std::setfill('0')
                   << std::hex << data << ")" << std::endl;
    }
    *m_dump_fh << std::endl;

    m_dump_fh->flush();
}
