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

import sys
from pathlib import Path
from time import sleep
from timeit import default_timer as timer

import grpc
from google.protobuf.empty_pb2 import Empty

import nexus_pb2_grpc
from nexus_pb2 import (NXControlInterval, NXControlActive, NXMeshLoadInstruction,
                       NXMeshMapOutput)

from nxmodel.base import Base
from nxmodel.manager import Manager
from nxmodel.message import ConfigureOutput, LoadInstruction

if __name__ == "__main__":
    # Setup link
    channel = grpc.insecure_channel("localhost:51234")
    stub    = nexus_pb2_grpc.NXServiceStub(channel)
    # Reset the device
    print("# Resetting the device")
    stub.ControlSetReset(Empty())
    sleep(0.1)
    # Get the current status
    def get_status(silent=False):
        if not silent: print("# Reading back status")
        status = stub.ControlGetStatus(Empty())
        if not silent:
            print(
                f"# State - Active: {status.active}, Idle Low: {status.seen_idle_low}, "
                f"First Tick: {status.first_tick}, Interval Set: {status.interval_set}"
            )
        return status
    get_status()
    # Disable logging from nxmodel
    class DummyLog:
        def error(*_args, **_kwargs): pass
        def warn(*_args, **_kwargs): pass
        def info(*_args, **_kwargs): pass
        def debug(*_args, **_kwargs): pass
    Base.LOG = DummyLog()
    # Load design from file
    print(f"# Loaded design: {sys.argv[1]}")
    mngr = Manager(None, None, 0, False)
    mngr.load(Path(sys.argv[1]))
    # Write into the design
    print(f"# Converting {len(mngr.queue)} queued messages")
    for msg in mngr.queue:
        if isinstance(msg, ConfigureOutput):
            stub.MeshMapOutput(NXMeshMapOutput(
                row=msg.row, column=msg.col, index=msg.src_idx,
                target_row=msg.tgt_row, target_column=msg.tgt_col,
                target_index=msg.tgt_idx, target_sequential=msg.tgt_seq
            ))
        elif isinstance(msg, LoadInstruction):
            stub.MeshLoadInstruction(NXMeshLoadInstruction(
                row=msg.row, column=msg.col, encoded=msg.instr.raw
            ))
        else:
            raise Exception(f"Unsupported message: {msg}")
    print("# Wrote all messages into the design")
    # Setup to run for one cycle
    print("# Setting up a 1 cycle interval")
    get_status()
    # Run for 2 cycles
    rtl_state = {}
    start     = timer()
    for idx in range(100):
        # Activate
        stub.ControlSetInterval(NXControlInterval(interval=1))
        stub.ControlSetActive(NXControlActive(active=True))
        while get_status(silent=True).active:
            sleep(0.1)
        # Get the current output state
        state = stub.MeshGetOutputState(Empty())
        print(f"State {idx:03d}: {state.state:016b}")
    delta = timer() - start
    print(f"Delta: {delta}")
