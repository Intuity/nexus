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

#ifndef __NXMEMORY_HPP__
#define __NXMEMORY_HPP__

#include <map>
#include <fstream>

namespace NXModel {

    template <class T, unsigned int W = 32>
    class NXMemory {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXMemory ( )
            : m_dump_fh ( NULL )
        { }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /**
         * @brief Clear the contents of the memory
         */
        void clear ( void )
        {
            m_contents.clear();
        }

        /**
         * @brief Write an item into the memory with a mask
         * @param address   Row address
         * @param data      Data to write
         * @param mask      Mask to modify existing data
         */
        void write ( uint32_t address, T data, T mask = -1 )
        {
            m_contents[address] = (
                ((read(address, 0)) & ~mask) |
                ((data            ) &  mask)
            );
        }

        /**
         * @brief Read from the memory, returning a default value if the address
         *        has not yet been populated
         * @param address   Row address
         * @param def_value Default value to return if not populated
         * @return          Value contained at address or default if not populated
         */
        T read ( uint32_t address, T def_value = 0 )
        {
            return populated(address) ? m_contents[address] : def_value;
        }

        /**
         * @brief Check if a given address has been populated
         * @param address   Row address
         * @return          True if populated, false if not
         */
        bool populated ( uint32_t address )
        {
            return m_contents.find(address) != m_contents.end();
        }

        /**
         * @brief Dump populated areas of memory image to a file
         * @param path  Where to dump the address
         * @param cycle Current cycle
         */
        void dump ( std::string path, unsigned int cycle )
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
                uint16_t data = entry.second;
                *m_dump_fh << std::setw(4) << std::setfill('0') << std::dec << (unsigned int)row;
                *m_dump_fh << " :";
                for (int offset = (W - 8); offset >= 0; offset -= 8) {
                    unsigned int chunk = (data >> offset) & 0xFF;
                    *m_dump_fh << " " << std::bitset<8>(chunk);
                }
                *m_dump_fh << " (0x" << std::setw(8) << std::setfill('0')
                        << std::hex << data << ")" << std::endl;
            }
            *m_dump_fh << std::endl;

            m_dump_fh->flush();
        }

    private:
        // =====================================================================
        // Private Members
        // =====================================================================
        std::map<uint32_t, T>   m_contents;
        std::fstream          * m_dump_fh;

    };

}

#endif // __NXMEMORY_HPP__
