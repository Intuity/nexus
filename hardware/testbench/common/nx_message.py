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

def payload_load_instr(core, instr):
    payload  = core  << 20
    payload |= instr << 5
    return payload

def payload_map_input(index, is_seq, rem_row, rem_col, rem_idx):
    payload  = rem_row << 17
    payload |= rem_col << 13
    payload |= rem_idx << 10
    payload |= index   <<  7
    payload |= is_seq  <<  6
    return payload

def payload_map_output(index, slot, send_bc, rem_row, rem_col):
    payload  = rem_row << 17
    payload |= rem_col << 13
    payload |= index   <<  7
    payload |= slot    <<  6
    payload |= send_bc <<  5
    return payload

def payload_sig_state(state, row, col, index):
    payload  = row   << 17
    payload |= col   << 13
    payload |= index << 10
    payload |= state <<  9
    return payload

def build_message(command, broadcast, tgt_row, tgt_col, bc_decay, *args, **kwargs):
    # Generate the payload
    payload = {
        Command.LOAD_INSTR: payload_load_instr,
        Command.INPUT     : payload_map_input,
        Command.OUTPUT    : payload_map_output,
        Command.SIG_STATE : payload_sig_state,
    }[command](*args, **kwargs)
    # Build the message
    msg = broadcast     << 31 # [   31] Broadcast flag
    if broadcast:
        msg |= bc_decay << 23 # [30:23] Broadcast decay
    else:
        msg |= tgt_row  << 27 # [30:27] Target row
        msg |= tgt_col  << 23 # [26:23] Target column
    msg |= int(command) << 21 # [22:21] Command
    msg |= payload            # [20: 0] Payload
    # Return the compiled message
    return msg

def build_load_instr(*args, **kwargs):
    return build_message(Command.LOAD_INSTR, *args, **kwargs)

def build_map_input(*args, **kwargs):
    return build_message(Command.INPUT, *args, **kwargs)

def build_map_output(*args, **kwargs):
    return build_message(Command.OUTPUT, *args, **kwargs)

def build_sig_state(*args, **kwargs):
    return build_message(Command.SIG_STATE, *args, **kwargs)
