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

#ifndef __NX_DEVICE_HPP__
#define __NX_DEVICE_HPP__

#include "nx_pipe.hpp"
#include "nx_constants.hpp"

namespace Nexus {

    // NXDevice
    // Abstracted interface for interacting with Nexus hardware
    //
    class NXDevice
    {
    public:
        // =====================================================================
        // Constructor
        // =====================================================================
        NXDevice(NXPipe * ctrl_pipe, NXPipe * mesh_pipe)
            : m_ctrl_pipe(ctrl_pipe)
            , m_mesh_pipe(mesh_pipe)
        { }

        // =====================================================================
        // Public Methods
        // =====================================================================
        bool            identify (void);
        nx_parameters_t read_parameters (void);

    private:
        // =====================================================================
        // Private Methods
        // =====================================================================

        // =====================================================================
        // Private Members
        // =====================================================================
        NXPipe * m_ctrl_pipe;
        NXPipe * m_mesh_pipe;

    };

}

#endif // __NX_DEVICE_HPP__
