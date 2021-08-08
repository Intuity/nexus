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

from nx_constants import ControlCommand

def payload_param(param):
    return param << 25 # [27:25] Parameter

def payload_active(active):
    return active << 27 # [27] Active

def payload_interval(interval):
    return interval << 0 # [27:0] Interval

def build_message(command, payload, *args, **kwargs):
    # Build the message
    msg = command << 28                                   # [30:28] Command
    if callable(payload): msg |= payload(*args, **kwargs) # [27: 0] Payload
    else                : msg |= payload                  # [27: 0] Payload
    # Return the compiled message
    return msg

def build_req_id(*args, **kwargs):
    return build_message(ControlCommand.ID, 0, *args, **kwargs)

def build_req_version(*args, **kwargs):
    return build_message(ControlCommand.VERSION, 0, *args, **kwargs)

def build_req_param(*args, **kwargs):
    return build_message(ControlCommand.PARAM, payload_param, *args, **kwargs)

def build_set_active(*args, **kwargs):
    return build_message(ControlCommand.ACTIVE, payload_active, *args, **kwargs)

def build_req_status(*args, **kwargs):
    return build_message(ControlCommand.STATUS, 0, *args, **kwargs)

def build_req_cycles(*args, **kwargs):
    return build_message(ControlCommand.CYCLES, 0, *args, **kwargs)

def build_set_interval(*args, **kwargs):
    return build_message(ControlCommand.INTERVAL, payload_interval, *args, **kwargs)

def build_soft_reset(*args, **kwargs):
    return build_message(ControlCommand.SOFT_RESET, 1, *args, **kwargs)
