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

    for msg_idx in range(1000):
        # Choose a random direction
        dirx = choice(list(Direction))

        # Choose a random command type
        command = choice(list(Command))

        # Select a random target row and column (ignored by decoder)
        tgt_row, tgt_col = randint(0, 15), randint(0, 15)

        # Generate a message
        msg = 0
        if command == Command.LOAD_INSTR:
            instr = randint(0, (1 << 15) - 1)
            msg   = build_load_instr(tgt_row, tgt_col, instr)
            dut.debug(f"MSG {msg_idx:03d}: Loading instruction 0x{instr:08X}")
            dut.exp_instr.append(InstrStore(instr))
        elif command == Command.OUTPUT:
            index   = randint(0,  7)
            rem_idx = randint(0,  7)
            is_seq  = choice((0, 1))
            msg     = build_map_output(
                tgt_row, tgt_col, index, tgt_row, tgt_col, rem_idx, is_seq
            )
            dut.debug(
                f"MSG {msg_idx:03d}: Map output - TR: {tgt_row}, TC: {tgt_col}, "
                f"LI: {index}, RI: {rem_idx}, SEQ: {is_seq}"
            )
            dut.exp_io.append(IOMapping(
                index, tgt_row, tgt_col, rem_idx, is_seq
            ))
        elif command == Command.SIG_STATE:
            index  = randint(0, 7)
            is_seq = choice((0, 1))
            state  = choice((0, 1))
            msg    = build_sig_state(tgt_row, tgt_col, index, is_seq, state)
            dut.debug(
                f"MSG {msg_idx:03d}: Signal state - TR: {tgt_row}, TC: {tgt_col}, "
                f"I: {index}, SEQ: {is_seq}, STATE: {state}"
            )
            dut.exp_state.append(SignalState(index, is_seq, state))
        elif command == Command.CONTROL:
            msg = (
                (tgt_row << 27) |
                (tgt_col << 23) |
                (int(command) << 21) |
                randint(0, (1 << 21) - 1)
            )
            dut.debug(f"MSG {msg_idx:03d}: Sending control 0x{msg:08X}")

        # Create a message
        dut.debug(
            f"MSG - R: {tgt_row}, C: {tgt_col}, CMD: {command} -> 0x{msg:08X}"
        )

        # Queue up the message
        dut.msg.append((msg, int(dirx)))
