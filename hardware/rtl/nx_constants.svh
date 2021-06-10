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

`ifndef __NX_CONSTANTS_SVH__
`define __NX_CONSTANTS_SVH__

typedef enum logic [1:0] {
    DIRX_NORTH, // 0 - Arriving from/sending to the north
    DIRX_EAST,  // 1 - ...the east
    DIRX_SOUTH, // 2 - ...the south
    DIRX_WEST   // 3 - ...the west
} nx_direction_t;

typedef enum logic [1:0] {
    CMD_LOAD_INSTR, // 0: Load an instruction
    CMD_CFG_INPUT,  // 1: Configure an input mapping
    CMD_CFG_OUTPUT, // 2: Configure an output mapping
    CMD_SIG_STATE   // 3: Signal state message
} nx_command_t;

`endif // __NX_CONSTANTS_SVH__
