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

#ifndef __NXMEMORY_HPP__
#define __NXMEMORY_HPP__

#include <map>

namespace NXModel {

    class NXMemory {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        NXMemory ( ) { }

        // =====================================================================
        // Public Methods
        // =====================================================================

        /**
         * @brief Clear the contents of the memory
         */
        void clear ( void );

        /**
         * @brief Write an item into the memory with a mask
         * @param address   Word address (4-byte aligned)
         * @param data      32-bit data
         * @param mask      32-bit mask
         */
        void write ( uint32_t address, uint32_t data, uint32_t mask = 0xFFFFFFFF );

        /**
         * @brief Read from the memory, returning a default value if the address
         *        has not yet been populated
         * @param address   Word address (4-byte aligned)
         * @param def_value Default value to return if not populated
         * @return          Value contained at address or default if not populated
         */
        uint32_t read ( uint32_t address, uint32_t def_value = 0 );

        /**
         * @brief Check if a given address has been populated
         * @param address   Word address (4-byte aligned)
         * @return          True if populated, false if not
         */
        bool populated ( uint32_t address );

    private:
        // =====================================================================
        // Private Members
        // =====================================================================
        std::map<uint32_t, uint32_t> m_contents;

    };

}

#endif // __NXMEMORY_HPP__
