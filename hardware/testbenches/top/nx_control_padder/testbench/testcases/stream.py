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
from cocotb.triggers import RisingEdge

from nxconstants import (ControlRespType, ControlResponsePadding, CONTROL_WIDTH,
                         SLOTS_PER_PACKET)

from drivers.stream.common import StreamTransaction

async def stream(dut, backpressure):
    """ Stream full and partial packets through the padder """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Optionally enable backpressure on outbound stream
    dut.outbound.delays = backpressure

    # Run for many iterations
    for _ in range(100):
        # Determine whether to emit full packet
        emit_full = choice((True, False))

        # Determine number of slots to fill
        num_slots = SLOTS_PER_PACKET if emit_full else randint(1, SLOTS_PER_PACKET)

        # Generate 'real' packets
        for idx in range(num_slots):
            data = randint(0, (1 << CONTROL_WIDTH) - 1)
            dut.inbound.append(StreamTransaction(data, last=(idx == (num_slots - 1))))
            dut.expected.append(StreamTransaction(data, last=(idx == (SLOTS_PER_PACKET - 1))))

        # Generate padding packets
        for idx in range(num_slots, SLOTS_PER_PACKET):
            resp         = ControlResponsePadding()
            resp.format  = ControlRespType.PADDING
            resp.entries = (SLOTS_PER_PACKET - idx)
            dut.expected.append(StreamTransaction(resp.pack(), last=(idx == (SLOTS_PER_PACKET - 1))))

        await dut.inbound.idle()
        while len(dut.expected) > 0: await RisingEdge(dut.clk)

factory = TestFactory(stream)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
