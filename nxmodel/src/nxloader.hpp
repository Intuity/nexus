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
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include "nexus.hpp"

#ifndef __NXLOADER_HPP__
#define __NXLOADER_HPP__

namespace NXModel {

    class NXLoader {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================
        NXLoader (Nexus * model, std::filesystem::path path);
        NXLoader (Nexus * model, std::string           path);

    private:

        // =====================================================================
        // Private Methods
        // =====================================================================

        void load(Nexus * model, std::filesystem::path path);

    };

}

#endif // __NXLOADER_HPP__
