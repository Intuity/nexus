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

`ifndef __NX_COMMANDS_SVH__
`define __NX_COMMANDS_SVH__

typedef enum bit [2:0] {
    CMD_LOAD_INSTR, // 0: Load an instruction into a logic core
    CMD_LAST_INSTR, // 1: Last instruction to load into a logic core
    CMD_BIT_VALUE,  // 2: Transfer a bit value between logic cores and boundary I/O
    CMD_OUT_MAP     // 3: Setup mapping of output bit to input bit
} nx_command_t;

`endif // __NX_COMMANDS_SVH__
