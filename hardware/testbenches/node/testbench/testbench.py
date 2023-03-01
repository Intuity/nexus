# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from random import randint
from types import SimpleNamespace

from forastero import BaseBench, IORole

from drivers.stream.io import StreamIO
from drivers.stream.common import StreamTransaction
from drivers.stream.init import StreamInitiator
from drivers.stream.resp import StreamResponder
from nxconstants import NodeID
from nxmodel import direction_t, NXMessagePipe, NXNode, node_raw_t, pack_node_raw, unpack_node_raw

class Testbench(BaseBench):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut, clk="clk", rst="rst")
        # Store the node ID
        self.node_id = NodeID(row=0, column=0)
        # Wrap I/Os
        self.trigger = SimpleNamespace(input =self.dut.i_trigger,
                                       output=self.dut.o_trigger)
        self.idle    = SimpleNamespace(input =self.dut.i_idle,
                                       output=self.dut.o_idle)
        # Register message interface initiator & responder drivers
        for dirx in ("north", "east", "south", "west"):
            self.register_driver(f"ib_{dirx}",
                                 StreamInitiator(self,
                                                 self.clk,
                                                 self.rst,
                                                 StreamIO(self.dut,
                                                          f"ib_{dirx}",
                                                          IORole.RESPONDER),
                                                 sniffer=self.drive_model))
            self.register_monitor(f"ob_{dirx}",
                                  StreamResponder(self,
                                                  self.clk,
                                                  self.rst,
                                                  StreamIO(self.dut,
                                                           f"ob_{dirx}",
                                                           IORole.INITIATOR)))
        # Create an array of all inbound & outbound interfaces
        self.all_inbound = [self.ib_north, self.ib_east, self.ib_south, self.ib_west]
        self.all_outbound = [self.ob_north, self.ob_east, self.ob_south, self.ob_west]
        # Create model instance
        self.model          = NXNode(0, 0, False)
        self.model_inbound  = [self.model.get_pipe(direction_t(x)) for x in range(4)]
        self.model_outbound = [NXMessagePipe() for _ in range(4)]
        for idx, pipe in enumerate(self.model_outbound):
            self.model.attach(direction_t(idx), pipe)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        for ob in self.all_outbound:
            ob.intf.set("present", 1)
        self.node_id = NodeID(row=randint(0, 15), column=randint(0, 15))
        self.dut.i_node_id.value = self.node_id.pack()
        self.idle.input.value    = 1
        self.trigger.input.value = 0
        self.model.reset()
        self.model.set_node_id(self.node_id.row, self.node_id.column)

    def drive_model(self,
                    driver      : StreamInitiator   = None,
                    transaction : StreamTransaction = None,
                    trigger     : bool              = False,
                    check_wait  : bool              = False) -> None:
        """ Apply the same stimulus to the model as the design """
        # Queue the transaction into the model
        if transaction:
            if driver is self.ib_north:
                self.model_inbound[direction_t.NORTH].enqueue(unpack_node_raw(transaction.data))
            elif driver is self.ib_east:
                self.model_inbound[direction_t.EAST].enqueue(unpack_node_raw(transaction.data))
            elif driver is self.ib_south:
                self.model_inbound[direction_t.SOUTH].enqueue(unpack_node_raw(transaction.data))
            elif driver is self.ib_west:
                self.model_inbound[direction_t.WEST].enqueue(unpack_node_raw(transaction.data))
        # Wait for the model to digest and return to idle
        while True:
            self.model.step(trigger)
            if self.model.is_idle() or (check_wait and self.model.is_waiting()):
                break
        # Pickup any outbound packets
        for idx, ob in enumerate(self.model_outbound):
            while not ob.is_idle():
                raw = node_raw_t()
                ob.dequeue(raw)
                tran = StreamTransaction(data=pack_node_raw(raw))
                self.all_outbound[idx].expected.append(tran)
