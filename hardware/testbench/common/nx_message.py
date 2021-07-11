# Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nx_constants import Command

def payload_load_instr(instr):
    return instr << 7

def payload_map_output(index, tgt_row, tgt_col, tgt_idx, tgt_seq):
    payload  = index   << 19
    payload |= tgt_row << 15
    payload |= tgt_col << 11
    payload |= tgt_idx <<  8
    payload |= tgt_seq <<  7
    return payload

def payload_sig_state(index, is_seq, state):
    payload  = index  << 19
    payload |= is_seq << 18
    payload |= state  << 17
    return payload

def build_message(command, payload, tgt_row, tgt_col, *args, **kwargs):
    # Build the message
    msg  = tgt_row      << 28                             # [31:28] Target row
    msg |= tgt_col      << 24                             # [27:24] Target column
    msg |= int(command) << 22                             # [23:22] Command
    if callable(payload): msg |= payload(*args, **kwargs) # [21: 0] Payload
    else                : msg |= payload                  # [21: 0] Payload
    # Return the compiled message
    return msg

def build_load_instr(*args, **kwargs):
    return build_message(Command.LOAD_INSTR, payload_load_instr, *args, **kwargs)

def build_map_output(*args, **kwargs):
    return build_message(Command.OUTPUT, payload_map_output, *args, **kwargs)

def build_sig_state(*args, **kwargs):
    return build_message(Command.SIG_STATE, payload_sig_state, *args, **kwargs)

def build_control(tgt_row, tgt_col, payload):
    return build_message(Command.CONTROL, payload, tgt_row, tgt_col)
