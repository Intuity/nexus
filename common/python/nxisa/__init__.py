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

from .instructions import MemoryDef, WaitDef, TruthDef, PickDef, ShuffleDef

# Create instruction objects
Memory  = MemoryDef()
Wait    = WaitDef()
Truth   = TruthDef()
Pick    = PickDef()
Shuffle = ShuffleDef()

# Lint guard
assert all((Memory, Wait, Truth, Pick, Shuffle))

# Pseudo-encodings
def Load(address, offset, tgt, comment=""):
    return Memory(offset      =offset,
                  address_6_0 =(address & 0x7F),
                  mode        =Memory.mode.LOAD,
                  tgt         =tgt,
                  address_10_7=((address >> 7) & 0x0F),
                  send_row    =0,
                  send_col    =0,
                  src         =0,
                  comment     =comment)

def Store(src, address, offset, comment=""):
    return Memory(offset      =offset,
                  address_6_0 =(address & 0x7F),
                  address_10_7=((address >> 7) & 0x0F),
                  mode        =Memory.mode.STORE,
                  tgt         =0,
                  send_row    =0,
                  send_col    =0,
                  src         =src,
                  comment     =comment)

def Send(src, row, column, address, offset, comment=""):
    return Memory(offset=offset,
                  address_6_0 =(address & 0x7F),
                  address_10_7=((address >> 7) & 0x0F),
                  mode        =Memory.mode.SEND,
                  tgt         =0,
                  send_row    =row,
                  send_col    =column,
                  src         =src,
                  comment     =comment)
