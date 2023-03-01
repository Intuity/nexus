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

from random import choice, randint

from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import MemorySlot, NodeCommand, NodeHeader, NodeLoad, NodeSignal
from nxconstants import NodeRaw, MAX_ROW_COUNT, MAX_COLUMN_COUNT, MESSAGE_WIDTH
from nxisa import Memory, Pause, Pick, Shuffle, Truth
from nxisa.fields import Target

from ..testbench import Testbench

@Testbench.testcase()
async def execute(tb):
    """ Random instruction sequence execution """
    # Generate and load an instruction sequence
    for instr_idx in range(1024):
        # Only allow PAUSE after the first 250 instructions
        options = [Memory, Pick, Shuffle, Truth]
        if instr_idx >= 250:
            options.append(Pause)
        # Select a random instruction
        instr = choice(options)
        # Randomise field values
        fvals = {}
        def _rand_fval(field):
            # If enumerated, only select from legal values
            if field.values:
                return choice(list(field.values.keys()))
            # Target register 7 only supported by TRUTH operation
            elif isinstance(field, Target):
                return randint(0, 6)
            # Otherwise randomise the field value
            else:
                return randint(0, field.mask)
        for group, entry in instr.fields.items():
            if isinstance(entry, list):
                fvals[group] = [_rand_fval(x) for x in entry]
            else:
                fvals[group] = _rand_fval(entry)
        # The final instruction must be a PAUSE with IDLE set
        if instr_idx == 1023:
            instr = Pause
            fvals = { "idle": True, "pc0": choice((True, False)) }
        # Encode the instruction
        encoded = instr.encode(fields=fvals)
        if instr_idx < 10:
            tb.info(f"INSTR {instr_idx:2d} - 0x{encoded:08X} - {instr.opcode.op_name} - {fvals}")
        # Load into memory
        for seg_idx in range(4):
            msg = NodeLoad(header =NodeHeader(target =tb.node_id.pack(),
                                              command=NodeCommand.LOAD).pack(),
                           address=(instr_idx << 1) | (seg_idx >> 1),
                           slot   =(seg_idx & 0x1),
                           data   =(encoded >> (seg_idx * 8)) & 0xFF)
            tb.ib_north.append(StreamTransaction(data=msg.pack()))

    # Generate and load the data memory
    for i_row in range(1024):
        for i_slot in range(4):
            msg = NodeSignal(header =NodeHeader(target =tb.node_id.pack(),
                                                command=NodeCommand.SIGNAL).pack(),
                             address=(i_row << 1) | (i_slot >> 1),
                             slot   =[MemorySlot.LOWER, MemorySlot.UPPER][(i_slot & 0x1)],
                             data   =randint(0, 255))
            tb.ib_north.append(StreamTransaction(data=msg.pack()))

    # Wait for drivers to go idle
    tb.info("Waiting for instructions and memory to be loaded")
    await tb.ib_north.idle()
    await ClockCycles(tb.clk, 10)

    # Check the memory state before running the program
    for row in range(1024):
        mdl_row = ((tb.model.read_data_memory((row * 2) + 1) << 16) |
                   (tb.model.read_data_memory((row * 2)    )      ))
        dut_row = int(tb.dut.u_dut.u_data_ram.memory[row].value)
        if mdl_row != dut_row:
            tb.error(f"Data {row:4d} - Model: 0x{mdl_row:08X}, "
                     f"DUT: 0x{dut_row:08X} [{' ' if dut_row == mdl_row else '!'}]")
        assert mdl_row == dut_row

    # Trigger the model and allow it to run to a idle/waiting state
    tb.info("Triggering the model")
    tb.drive_model(trigger=True, check_wait=True)

    # Trigger the DUT
    tb.info("Triggering the DUT")
    await RisingEdge(tb.clk)
    tb.trigger.input.value = 1
    await RisingEdge(tb.clk)
    tb.trigger.input.value = 0

    # Wait for the DUT to become active
    tb.info("Waiting for DUT to become active")
    while tb.idle.output.value == 1:
        await RisingEdge(tb.clk)

    # Wait for the DUT to pause
    tb.info("Waiting for DUT to pause")
    while tb.dut.u_dut.u_core.pause_q.value == 0:
        await RisingEdge(tb.clk)

    # Check the PC
    mdl_pc = tb.model.get_pc()
    dut_pc = int(tb.dut.u_dut.u_core.pc_fetch_q.value)
    tb.info(f"PC - Model: 0x{mdl_pc:04X}, DUT: 0x{dut_pc:04X}")
    assert mdl_pc == dut_pc, "PC mismatch between model and DUT"

    # Check the registers
    mismatches = 0
    for reg_idx in range(8):
        mdl_val = tb.model.get_register(reg_idx)
        dut_val = int(tb.dut.u_dut.u_core.regfile_q.value[((7-reg_idx)*8):((7-reg_idx)*8)+7])
        tb.info(f"R{reg_idx} - Model: 0x{mdl_val:02X}, DUT: 0x{dut_val:02X} [{' ' if dut_val == mdl_val else '!'}]")
        mismatches += (mdl_val != dut_val)

    # Check the memory state
    for row in range(1024):
        mdl_row = ((tb.model.read_data_memory((row * 2) + 1) << 16) |
                   (tb.model.read_data_memory((row * 2)    )      ))
        dut_row = int(tb.dut.u_dut.u_data_ram.memory[row].value)
        if mdl_row != dut_row:
            tb.error(f"Data {row:4d} - Model: 0x{mdl_row:08X}, "
                     f"DUT: 0x{dut_row:08X} [{' ' if dut_row == mdl_row else '!'}]")
        mismatches += (mdl_row != dut_row)

    # Check for any mismatches
    assert mismatches == 0, f"{mismatches} mismatches between model and DUT"
