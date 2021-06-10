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
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.io import StreamDirection

from ..testbench import testcase

@testcase()
async def sanity(dut):
    """ Basic testcase """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Run for 100 clock cycles
    dut.info("Running for 100 clock cycles")
    await ClockCycles(dut.clk, 100)

    # All done!
    dut.info("Finished counting cycles")

async def broadcast(dut, backpressure):
    """ Check routing of a broadcast message """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Activate/deactivate backpressure
    dut.bypass.delays = backpressure

    # Generate many random messages
    for _ in range(1000):
        # Choose a random direction
        dirx = choice(list(StreamDirection))

        # Form and queue a broadcast message
        command = randint(0, (1 <<  2) - 1)
        payload = randint(0, (1 << 21) - 1)
        msg  = (1       << 31) # [   31] Broadcast flag
        msg |= (8       << 23) # [30:23] Broadcast decay
        msg |= (command << 21) # [22:21] Command
        msg |= (payload <<  0) # [20: 0] Payload
        dut.debug(f"Transmit message 0x{msg:08X}")
        dut.msg.append((msg, int(dirx)))

        # Should be received with decay less one
        bc_msg  = msg & 0x807F_FFFF
        bc_msg |= (7 << 23) # [30:23] Broadcast decay
        dut.debug(f"Expecting message 0x{bc_msg:08X}")
        if dirx == StreamDirection.NORTH: # Sends to east, south, & west
            dut.expected.append((bc_msg, int(StreamDirection.EAST )))
            dut.expected.append((bc_msg, int(StreamDirection.SOUTH)))
            dut.expected.append((bc_msg, int(StreamDirection.WEST )))
        elif dirx == StreamDirection.EAST: # Sends just to the west
            dut.expected.append((bc_msg, int(StreamDirection.WEST )))
        elif dirx == StreamDirection.SOUTH: # Sends to north, east, & west
            dut.expected.append((bc_msg, int(StreamDirection.NORTH)))
            dut.expected.append((bc_msg, int(StreamDirection.EAST )))
            dut.expected.append((bc_msg, int(StreamDirection.WEST )))
        elif dirx == StreamDirection.WEST: # Sends just to the east
            dut.expected.append((bc_msg, int(StreamDirection.EAST )))

factory = TestFactory(broadcast)
factory.add_option("backpressure", [True, False])
factory.generate_tests()

@testcase()
async def redirect(dut):
    """ Check that messages are redirected correctly """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Activate/deactivate backpressure
    dut.bypass.delays = True

    for _ in range(1000):
        # Choose a random target (that is not the same as this cell)
        tgt_row, tgt_col = 0, 0
        while True:
            tgt_row, tgt_col = randint(0, 15), randint(0, 15)
            if tgt_row != row or tgt_col != col: break

        # Form and send an addressed message
        command = randint(0, (1 <<  2) - 1)
        payload = randint(0, (1 << 21) - 1)
        msg  = (0       << 31) # [   31] Broadcast flag
        msg |= (tgt_row << 27) # [30:27] Target row
        msg |= (tgt_col << 23) # [26:23] Target column
        msg |= (command << 21) # [22:21] Command
        msg |= (payload <<  0) # [20: 0] Payload
        dut.debug(f"Transmit message 0x{msg:08X} to {tgt_row}, {tgt_col}")
        dut.msg.append((msg, int(choice(list(StreamDirection)))))

        # Queue up the expected message
        if   tgt_row < row: dut.expected.append((msg, int(StreamDirection.NORTH)))
        elif tgt_row > row: dut.expected.append((msg, int(StreamDirection.SOUTH)))
        elif tgt_col < col: dut.expected.append((msg, int(StreamDirection.WEST )))
        elif tgt_col > col: dut.expected.append((msg, int(StreamDirection.EAST )))
