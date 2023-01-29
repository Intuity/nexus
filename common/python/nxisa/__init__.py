# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from .base import Label
from .instrdef import Instance
from .instructions import MemoryDef, PauseDef, TruthDef, PickDef, ShuffleDef
from .utility import dump_asm, dump_hex

assert all((Instance, Label, dump_asm, dump_hex))

# Create instruction objects
Memory  = MemoryDef()
Pause   = PauseDef()
Truth   = TruthDef()
Pick    = PickDef()
Shuffle = ShuffleDef()

# Lint guard
assert all((Memory, Pause, Truth, Pick, Shuffle))

# Pseudo-encodings
def Load(address, slot, tgt, comment=""):
    return Memory(slot        =slot,
                  address_6_0 =(address & 0x7F),
                  mode        =Memory.mode.LOAD,
                  tgt         =tgt,
                  address_10_7=((address >> 7) & 0x0F),
                  send_row    =0,
                  send_col    =0,
                  src         =0,
                  comment     =comment)

def Store(src, address, slot, mask, comment=""):
    return Memory(slot        =slot,
                  address_6_0 =(address & 0x7F),
                  address_10_7=((address >> 7) & 0x0F),
                  mode        =Memory.mode.STORE,
                  tgt         =0,
                  send_row    =((mask >> 4) & 0x0F),
                  send_col    =((mask     ) & 0x0F),
                  src         =src,
                  comment     =comment)

def Send(src, row, column, address, slot, comment=""):
    return Memory(slot        =slot,
                  address_6_0 =(address & 0x7F),
                  address_10_7=((address >> 7) & 0x0F),
                  mode        =Memory.mode.SEND,
                  tgt         =0,
                  send_row    =row,
                  send_col    =column,
                  src         =src,
                  comment     =comment)

Load.slot  = Memory.slot
Store.slot = Memory.slot
Send.slot  = Memory.slot
