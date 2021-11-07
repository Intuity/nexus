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

from ..testbench import testcase
from drivers.memory.common import MemoryTransaction
from drivers.state.common import SignalState
from drivers.stream.common import StreamTransaction

from nxconstants import (NodeCommand, NodeMessage, MESSAGE_WIDTH, LOAD_SEG_WIDTH,
                         LB_SECTION_WIDTH, LB_SELECT_WIDTH, NodeParameter)

@testcase()
async def messages(dut):
    """ Send different types of messages to the DUT and check they are decoded """
    dut.info("Resetting the DUT")
    await dut.reset()

    # State
    load_addr  = 0
    load_accum = 0
    loopback   = 0
    num_instr  = 0
    num_output = 0

    for msg_idx in range(10000):
        # Generate a random message
        msg = NodeMessage()
        while True:
            try:
                msg.unpack(randint(0, (1 << MESSAGE_WIDTH) - 1))
                break
            except Exception:
                continue

        # Logging
        dut.debug(f"Message {msg_idx:4d} - {NodeCommand(msg.raw.header.command).name}")

        # LOAD: Accumulate data, write to memory when LAST flag goes high
        if msg.raw.header.command == NodeCommand.LOAD:
            # Calculate mask
            seg_mask = (1 << LOAD_SEG_WIDTH) - 1
            # Mask and shift the accumulated value and OR in the new data
            load_accum  = (load_accum & seg_mask) << LOAD_SEG_WIDTH
            load_accum |= msg.load.data & seg_mask
            # Write to memory if the LAST flag is set high
            if msg.load.last:
                dut.exp_ram.append(MemoryTransaction(
                    addr=load_addr, wr_data=load_accum, wr_en=1
                ))
                load_addr  = (load_addr + 1) if (load_addr < 1023) else 0
                load_accum = 0

        # LOOPBACK: Accumulate loopback mask in chunks
        elif msg.raw.header.command == NodeCommand.LOOPBACK:
            # Calculate section offset
            offset = LB_SECTION_WIDTH * (msg.loopback.select % 2)
            # Calculate mask and inverse mask
            mask      = ((1 << LB_SECTION_WIDTH) - 1) << offset
            full_mask = (1 << (LB_SECTION_WIDTH * (1 << LB_SELECT_WIDTH))) - 1
            inv_mask  = full_mask - mask
            # Update loopback
            updated = (loopback & inv_mask) | (msg.loopback.section << offset)
            # Append to queue (if value changed)
            if updated != loopback:
                dut.exp_lb_mask.append(updated)
            # Keep track of the previous value
            loopback = updated

        # SIGNAL: Signal state updates
        elif msg.raw.header.command == NodeCommand.SIGNAL:
            dut.exp_sig.append(SignalState(
                msg.signal.index, msg.signal.is_seq, msg.signal.state
            ))

        # CONTROL: Parameter updates
        elif msg.raw.header.command == NodeCommand.CONTROL:
            if (msg.control.param == NodeParameter.INSTRUCTIONS) and (msg.control.value != num_instr):
                dut.exp_num_instr.append(msg.control.value)
                num_instr = msg.control.value
            elif (msg.control.param == NodeParameter.OUTPUTS) and (msg.control.value != num_output):
                dut.exp_num_output.append(msg.control.value)
                num_output = msg.control.value

        # Queue up the message
        dut.msg.append(StreamTransaction(data=msg.pack()))
