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

from typing import List, Union
from pathlib import Path

from .base import Label
from .instrdef import Instance

# Dump to assembly file
def dump_asm(stream : List[Union[Instance, Label]], path : Path):
    address  = 0
    labelled = False
    with open(path, "w", encoding="utf-8") as fh:
        for entry in stream:
            if isinstance(entry, Label):
                fh.write(entry.to_asm() + "\n")
                labelled = True
            elif isinstance(entry, Instance):
                pfx = ["", "    "][labelled]
                fh.write(f"{pfx}{entry.to_asm(address)}\n")
                address += 1
            else:
                raise Exception(f"Unknown stream entry: {entry}")

# Dump to hex file
def dump_hex(stream : List[Union[Instance, Label]], path : Path):
    with open(path, "w", encoding="utf-8") as fh:
        for entry in stream:
            if isinstance(entry, Label):
                continue
            elif isinstance(entry, Instance):
                fh.write(f"{entry.encode():08X}\n")
            else:
                raise Exception(f"Unknown stream entry: {entry}")
