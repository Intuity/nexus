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

    # Raise active
    dut.active_i <= 1

    # Find the number of rows and columns
    num_rows = int(dut.dut.dut.ROWS)
    num_cols = int(dut.dut.dut.COLUMNS)

    for _ in range(1000):
        # Choose a random command type
        command = choice(list(Command))

        # Select a target row and column
        tgt_row, tgt_col = num_rows, 0

        # Generate a message
        msg = 0
        if command == Command.LOAD_INSTR:
            msg = build_load_instr(
                0, tgt_row, tgt_col, 0, choice((0, 1)),
                randint(0, (1 << 15) - 1),
            )
        elif command == Command.INPUT:
            msg = build_map_input(
                0, tgt_row, tgt_col, 0, randint(0, 7),
                choice((0, 1)), randint(0, 15), randint(0, 15), randint(0, 7),
            )
        elif command == Command.OUTPUT:
            msg = build_map_output(
                0, tgt_row, tgt_col, 0, randint(0,  7),
                choice((0, 1)), choice((0, 1)), randint(0, 15), randint(0, 15),
            )
        elif command == Command.SIG_STATE:
            msg = build_sig_state(
                0, tgt_row, tgt_col, 0, choice((0, 1)),
                randint(0, 15), randint(0, 15), randint(0,  7),
            )

        # Create a message
        dut.debug(
            f"MSG - R: {tgt_row}, C: {tgt_col}, CMD: {command} -> 0x{msg:08X}"
        )

        # Queue up the message
        dut.inbound.append(msg)
        dut.expected.append((msg, 0))
