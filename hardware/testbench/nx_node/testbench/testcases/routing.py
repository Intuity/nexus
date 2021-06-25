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

from nx_constants import Command, Direction
from nx_message import (build_load_instr, build_map_input, build_map_output,
                        build_sig_state)

from ..testbench import testcase

@testcase()
async def routing(dut):
    """ Exercise message routing through a node """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.info(f"Setting row to {row} & column to {col}")
    dut.node_row_i <= row
    dut.node_col_i <= col

    for _ in range(1000):
        # Choose a random command type
        # NOTE: Don't use SIG_STATE as this risks triggering an emitted message
        command = choice((
            Command.LOAD_INSTR, Command.INPUT, Command.OUTPUT,
        ))

        # Select a target row and column
        broadcast = choice((0, 1))
        bc_decay  = randint(1, 10)
        tgt_row, tgt_col = row, col
        if choice((0, 1)):
            tgt_row, tgt_col = randint(0, 15), randint(0, 15)

        # Check if this message is targeted at the node
        tgt_match = (tgt_row == row) and (tgt_col == col)

        # Generate a message
        msg = 0
        if command == Command.LOAD_INSTR:
            msg = build_load_instr(
                broadcast, tgt_row, tgt_col, bc_decay, choice((0, 1)),
                randint(0, (1 << 15) - 1),
            )
        elif command == Command.INPUT:
            msg = build_map_input(
                broadcast, tgt_row, tgt_col, bc_decay, randint(0, 7),
                choice((0, 1)), randint(0, 15), randint(0, 15), randint(0, 7),
            )
        elif command == Command.OUTPUT:
            msg = build_map_output(
                broadcast, tgt_row, tgt_col, bc_decay, randint(0,  7),
                choice((0, 1)), choice((0, 1)), randint(0, 15), randint(0, 15),
            )
        else:
            raise Exception(f"Unsupported {command = }")

        # Create a message
        dut.debug(
            f"MSG - BC: {broadcast}, R: {tgt_row}, C: {tgt_col}, CMD: {command} "
            f"-> 0x{msg:08X}"
        )

        # Generate bypass message
        byp_msg = msg
        if broadcast:
            byp_msg &= 0x807F_FFFF
            byp_msg |= (bc_decay - 1) << 23

        # Queue up the message
        in_pipe = choice(dut.inbound)
        in_dirx = Direction(dut.inbound.index(in_pipe))
        in_pipe.append(msg)

        # If not matching this target, expect message to be routed elsewhere
        if broadcast:
            if in_dirx == Direction.NORTH:
                dut.expected[int(Direction.EAST )].append((byp_msg, 0))
                dut.expected[int(Direction.SOUTH)].append((byp_msg, 0))
                dut.expected[int(Direction.WEST )].append((byp_msg, 0))
            elif in_dirx == Direction.EAST:
                dut.expected[int(Direction.WEST )].append((byp_msg, 0))
            if in_dirx == Direction.SOUTH:
                dut.expected[int(Direction.NORTH)].append((byp_msg, 0))
                dut.expected[int(Direction.EAST )].append((byp_msg, 0))
                dut.expected[int(Direction.WEST )].append((byp_msg, 0))
            elif in_dirx == Direction.WEST:
                dut.expected[int(Direction.EAST )].append((byp_msg, 0))
        elif not tgt_match:
            if   tgt_row < row: tgt_dirx = Direction.NORTH
            elif tgt_row > row: tgt_dirx = Direction.SOUTH
            elif tgt_col < col: tgt_dirx = Direction.WEST
            elif tgt_col > col: tgt_dirx = Direction.EAST
            dut.expected[int(tgt_dirx)].append((byp_msg, 0))
