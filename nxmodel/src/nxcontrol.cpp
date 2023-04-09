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

#include <assert.h>
#include <bitset>
#include <iomanip>
#include <sstream>

#include <plog/Log.h>

#include "nxcontrol.hpp"

using namespace NXModel;
using namespace NXConstants;

void NXControl::reset (void)
{
    if (m_to_mesh   != nullptr) m_to_mesh->reset();
    if (m_from_mesh != nullptr) m_from_mesh->reset();
}

bool NXControl::is_idle (void)
{
    return m_to_mesh->is_idle() && m_from_mesh->is_idle();
}

void NXControl::step (void)
{
    // ...todo...
}
