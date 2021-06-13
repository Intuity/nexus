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

from drivers.instr.store import InstrStore

from ..testbench import testcase
from drivers.map_io.common import IOMapping
from drivers.state.common import SignalState

from nx_constants import Command, Direction
from nx_message import (build_load_instr, build_map_input, build_map_output,
                        build_sig_state)

@testcase()
async def messages(dut):
    """ Send different types of messages to the DUT and check they are decoded """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    for _ in range(1000):
        # Choose a random direction
        dirx = choice(list(Direction))

        # Choose a random command type
        command = choice(list(Command))

        # Select a target row and column
        broadcast = choice((0, 1))
        bc_decay  = randint(1, 10)
        tgt_row, tgt_col = row, col
        if choice((True, False)):
            tgt_row, tgt_col = randint(0, 15), randint(0, 15)

        # Check if this message is targeted at the node
        tgt_match = (tgt_row == row) and (tgt_col == col)

        # Generate a message
        msg = 0
        if command == Command.LOAD_INSTR:
            core  = choice((0, 1))
            instr = randint(0, (1 << 15) - 1)
            msg   = build_load_instr(
                broadcast, tgt_row, tgt_col, bc_decay, core, instr,
            )
            if broadcast or tgt_match:
                dut.exp_instr.append(InstrStore(core, instr))
        elif command == Command.INPUT:
            index   = randint(0,  7)
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            rem_idx = randint(0,  7)
            is_seq  = choice((0, 1))
            msg     = build_map_input(
                broadcast, tgt_row, tgt_col, bc_decay, index, is_seq, rem_row,
                rem_col, rem_idx,
            )
            if broadcast or tgt_match:
                dut.exp_io.append(IOMapping(
                    index, 1, rem_row, rem_col, rem_idx, is_seq, 0, is_seq,
                ))
        elif command == Command.OUTPUT:
            index   = randint(0,  7)
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            slot    = choice((0, 1))
            send_bc = choice((0, 1))
            msg       = build_map_output(
                broadcast, tgt_row, tgt_col, bc_decay, index, slot, send_bc,
                rem_row, rem_col,
            )
            if broadcast or tgt_match:
                dut.exp_io.append(IOMapping(
                    index, 0, rem_row, rem_col, 0, slot, send_bc, slot,
                ))
        elif command == Command.SIG_STATE:
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            rem_idx = randint(0,  7)
            state   = choice((0, 1))
            msg     = build_sig_state(
                broadcast, tgt_row, tgt_col, bc_decay, state, rem_row, rem_col,
                rem_idx,
            )
            if broadcast or tgt_match:
                dut.exp_state.append(SignalState(
                    rem_row, rem_col, rem_idx, state,
                ))

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
        dut.msg.append((msg, int(dirx)))

        # If not matching this target, expect message to be routed elsewhere
        if broadcast:
            if dirx == Direction.NORTH:
                dut.exp_bypass.append((byp_msg, int(Direction.EAST) ))
                dut.exp_bypass.append((byp_msg, int(Direction.SOUTH)))
                dut.exp_bypass.append((byp_msg, int(Direction.WEST) ))
            elif dirx == Direction.EAST:
                dut.exp_bypass.append((byp_msg, int(Direction.WEST) ))
            if dirx == Direction.SOUTH:
                dut.exp_bypass.append((byp_msg, int(Direction.NORTH)))
                dut.exp_bypass.append((byp_msg, int(Direction.EAST) ))
                dut.exp_bypass.append((byp_msg, int(Direction.WEST) ))
            elif dirx == Direction.WEST:
                dut.exp_bypass.append((byp_msg, int(Direction.EAST) ))
        elif not tgt_match:
            if   tgt_row < row: tgt_dirx = Direction.NORTH
            elif tgt_row > row: tgt_dirx = Direction.SOUTH
            elif tgt_col < col: tgt_dirx = Direction.WEST
            elif tgt_col > col: tgt_dirx = Direction.EAST
            dut.exp_bypass.append((byp_msg, int(tgt_dirx)))
