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

from nxconstants import Direction, NodeCommand, NodeMessage

@testcase()
async def messages(dut):
    """ Send different types of messages to the DUT and check they are decoded """
    dut.info("Resetting the DUT")
    await dut.reset()

    for msg_idx in range(1000):
        # Choose a random direction
        dirx = choice(list(Direction))

        # Choose a random command type
        command = choice(list(NodeCommand))

        # Randomise message contents until legal
        msg = NodeMessage()
        while True:
            try:
                msg.unpack(randint(0, (1 << 31) - 1))
                break
            except Exception:
                continue

        # Setup the correct command
        msg.raw.header.command = command

        # Generate a message
        if command == NodeCommand.LOAD_INSTR:
            dut.debug(
                f"MSG {msg_idx:03d}: Loading instruction 0x{msg.load_instr.instr.pack():08X}"
            )
            dut.exp_instr.append(InstrStore(msg.load_instr.instr.pack()))
        elif command == NodeCommand.MAP_OUTPUT:
            dut.debug(
                f"MSG {msg_idx:03d}: Map output - TR: {msg.map_output.target_row}, "
                f"TC: {msg.map_output.target_column}, LI: {msg.map_output.source_index}, "
                f"RI: {msg.map_output.target_index}, SEQ: {msg.map_output.target_is_seq}"
            )
            dut.exp_io.append(IOMapping(
                msg.map_output.source_index, msg.map_output.target_row,
                msg.map_output.target_column, msg.map_output.target_index,
                msg.map_output.target_is_seq
            ))
        elif command == NodeCommand.SIG_STATE:
            dut.debug(
                f"MSG {msg_idx:03d}: I: {msg.sig_state.index}, "
                f"SEQ: {msg.sig_state.is_seq}, STATE: {msg.sig_state.state}"
            )
            dut.exp_state.append(SignalState(
                msg.sig_state.index, msg.sig_state.is_seq, msg.sig_state.state
            ))
        elif command == NodeCommand.NODE_CTRL:
            dut.debug(f"MSG {msg_idx:03d}: Sending control 0x{msg.raw.payload:08X}")

        # Create a message
        dut.debug(
            f"MSG - R: {msg.raw.header.row}, C: {msg.raw.header.column}, "
            f"CMD: {command}  -> 0x{msg.pack():08X}"
        )

        # Queue up the message
        dut.msg.append((msg.pack(), int(dirx)))
