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

from random import choice, randint

from cocotb.regression import TestFactory

async def bypass(dut, backpressure):
    """ Queue up messages randomly between internal and bypass interfaces """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Set the node address to a random value
    dut.node_row_i <= (row    := randint(1, 14))
    dut.node_col_i <= (column := randint(1, 14))

    # Activate/deactivate backpressure
    dut.int.delays = backpressure
    dut.byp.delays = backpressure

    # Get the width of the data
    intf_size = max(dut.int_io.data._range)-min(dut.int_io.data._range)+1

    # Function to generate messages
    def gen_msg():
        return [
            (
                (row << 28) | (column << 24)
                if choice((0, 1)) else
                randint(0, (1 << 8) - 1)
            ) |
            randint(0, (1 << (intf_size - 8)) - 1)
            for _ in range(randint(50, 100))
        ]

    # Queue up random messages onto the different drivers
    north, east, south, west = gen_msg(), gen_msg(), gen_msg(), gen_msg()

    for msg in north: dut.north.append(msg)
    for msg in east : dut.east.append(msg)
    for msg in south: dut.south.append(msg)
    for msg in west : dut.west.append(msg)

    # Construct the expected arbitration (using round robin)
    last = 0
    while north or east or south or west:
        for idx in range(4):
            dirx = (idx + last + 1) % 4
            data = None
            if   dirx == 0 and north: data = north.pop(0)
            elif dirx == 1 and east : data = east.pop(0)
            elif dirx == 2 and south: data = south.pop(0)
            elif dirx == 3 and west : data = west.pop(0)
            if not data: continue
            tgt_row = (data >> 28) & 0xF
            tgt_col = (data >> 24) & 0xF
            match   = (tgt_row == row) and (tgt_col == column)
            if match:
                dut.int_expected.append((data, 0))
            else:
                tgt_dir = 0
                if   tgt_row > row   : tgt_dir = 2
                elif tgt_row < row   : tgt_dir = 0
                elif tgt_col > column: tgt_dir = 1
                elif tgt_col < column: tgt_dir = 3
                dut.byp_expected.append((data, tgt_dir))
        # Capture the last direction
        last = dirx

factory = TestFactory(bypass)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
