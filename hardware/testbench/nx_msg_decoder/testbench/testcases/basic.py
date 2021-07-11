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

from cocotb.triggers import ClockCycles

from nx_constants import Direction

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

    # Unregister IO mapping, instruction, and signal state interfaces from monitor
    dut.instr_load._callbacks = []
    dut.io_map._callbacks     = []
    dut.state._callbacks      = []

    for _ in range(1000):
        # Choose a random target (that is not the same as this cell)
        tgt_row, tgt_col = 0, 0
        while True:
            tgt_row, tgt_col = randint(0, 15), randint(0, 15)
            if tgt_row != row or tgt_col != col: break

        # Form and send an addressed message
        command = randint(0, (1 <<  2) - 1)
        payload = randint(0, (1 << 22) - 1)
        msg  = (tgt_row << 28) # [31:28] Target row
        msg |= (tgt_col << 24) # [27:24] Target column
        msg |= (command << 22) # [23:22] Command
        msg |= (payload <<  0) # [21: 0] Payload
        dut.debug(f"Transmit message 0x{msg:08X} to {tgt_row}, {tgt_col}")
        dut.msg.append((msg, int(choice(list(Direction)))))

        # Queue up the expected message
        if   tgt_row < row: dut.exp_bypass.append((msg, int(Direction.NORTH)))
        elif tgt_row > row: dut.exp_bypass.append((msg, int(Direction.SOUTH)))
        elif tgt_col < col: dut.exp_bypass.append((msg, int(Direction.WEST )))
        elif tgt_col > col: dut.exp_bypass.append((msg, int(Direction.EAST )))
