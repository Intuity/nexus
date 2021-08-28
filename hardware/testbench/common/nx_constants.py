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

from enum import IntEnum

DEVICE_ID            = 0x4E5853
DEVICE_VERSION_MAJOR = 0
DEVICE_VERSION_MINOR = 3

class Direction(IntEnum):
    """ Direction of receival/transmission """
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3

class Command(IntEnum):
    """ Command type """
    LOAD_INSTR = 0
    OUTPUT     = 1
    SIG_STATE  = 2
    CONTROL    = 3

class ControlCommand(IntEnum):
    """ Control block command type """
    ID         = 0
    VERSION    = 1
    PARAM      = 2
    ACTIVE     = 3
    STATUS     = 4
    CYCLES     = 5
    INTERVAL   = 6
    SOFT_RESET = 7

class ControlParameter(IntEnum):
    """ Control block parameter type """
    COUNTER_WIDTH  = 0
    ROWS           = 1
    COLUMNS        = 2
    NODE_INPUTS    = 3
    NODE_OUTPUTS   = 4
    NODE_REGISTERS = 5
