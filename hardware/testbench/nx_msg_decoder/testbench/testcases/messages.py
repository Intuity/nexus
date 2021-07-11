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
from nx_message import build_load_instr, build_map_output, build_sig_state

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
        tgt_row, tgt_col = row, col
        if choice((True, False)):
            tgt_row, tgt_col = randint(0, 15), randint(0, 15)

        # Check if this message is targeted at the node
        tgt_match = (tgt_row == row) and (tgt_col == col)

        # Generate a message
        msg = 0
        if command == Command.LOAD_INSTR:
            instr = randint(0, (1 << 15) - 1)
            msg   = build_load_instr(tgt_row, tgt_col, instr)
            if tgt_match: dut.exp_instr.append(InstrStore(instr))
        elif command == Command.OUTPUT:
            index   = randint(0,  7)
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            rem_idx = randint(0,  7)
            is_seq  = choice((0, 1))
            msg     = build_map_output(
                tgt_row, tgt_col, index, rem_row, rem_col, rem_idx, is_seq
            )
            if tgt_match:
                dut.exp_io.append(IOMapping(
                    index, rem_row, rem_col, rem_idx, is_seq
                ))
        elif command == Command.SIG_STATE:
            index  = randint(0, 7)
            is_seq = choice((0, 1))
            state  = choice((0, 1))
            msg    = build_sig_state(tgt_row, tgt_col, index, is_seq, state)
            if tgt_match:
                dut.exp_state.append(SignalState(index, is_seq, state))

        # Create a message
        dut.debug(
            f"MSG - R: {tgt_row}, C: {tgt_col}, CMD: {command} -> 0x{msg:08X}"
        )

        # Queue up the message
        dut.msg.append((msg, int(dirx)))

        # If not matching this target, expect message to be routed elsewhere
        if not tgt_match:
            if   tgt_row < row: tgt_dirx = Direction.NORTH
            elif tgt_row > row: tgt_dirx = Direction.SOUTH
            elif tgt_col < col: tgt_dirx = Direction.WEST
            elif tgt_col > col: tgt_dirx = Direction.EAST
            dut.exp_bypass.append((msg, int(tgt_dirx)))
