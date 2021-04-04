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

import copy

from .base import Base

class Message(Base):
    """ Base class for a message """

    def __init__(self, env, tgt_row, tgt_col, broadcast=False, decay=0):
        """ Initialise Message instance.

        Args:
            env      : SimPy environment
            tgt_row  : Target node's row
            tgt_col  : Target node's column
            broadcast: Whether to broadcast the message
            decay    : How many steps to allow a broadcast message to propagate
        """
        super().__init__(env)
        assert isinstance(tgt_row, int) and tgt_row >= 0
        assert isinstance(tgt_col, int) and tgt_col >= 0
        assert broadcast in (True, False)
        assert isinstance(decay, int) and decay >= 0
        self.tgt_row   = tgt_row
        self.tgt_col   = tgt_col
        self.broadcast = broadcast
        self.decay     = decay

    @property
    def target(self): return self.tgt_row, self.tgt_col

    def copy(self):
        return copy.copy(self)

class LoadInstruction(Base):
    """ Load an instruction into a core """

    def __init__(self, env, tgt_row, tgt_col, slot, instr):
        """ Initialise the message.

        Args:
            env    : SimPy environment
            tgt_row: Target node's row
            tgt_col: Target node's column
            slot   : What instruction to load
            instr  : The instruction to load
        """
        super().__init__(env, tgt_row, tgt_col)
        self.slot  = slot
        self.instr = instr

class ConfigureInput(Base):
    """ Configure an input mapping """

    def __init__(
        self, env, tgt_row, tgt_col, src_row, src_col, src_pos, tgt_pos, state,
    ):
        """ Initialise the message.

        Args:
            env    : SimPy environment
            tgt_row: Target node's row
            tgt_col: Target node's column
            src_row: Source node's row
            src_col: Source node's column
            src_pos: Output position from the source node
            tgt_pos: Input position to fill with the data
            state  : Whether the input should be held until the next tick
        """
        super().__init__(env, tgt_row, tgt_col)
        self.src_row = src_row
        self.src_col = src_col
        self.src_pos = src_pos
        self.tgt_pos = tgt_pos
        self.state   = state

class ConfigureOutput(Base):
    """ Configure output messaging """

    def __init__(
        self, env, tgt_row, tgt_col, out_pos, msg_a_row, msg_a_col, msg_b_row,
        msg_b_col, msg_as_bc, bc_decay,
    ):
        """ Initialise the message.

        Args:
            env      : SimPy environment
            tgt_row  : Target node's row
            tgt_col  : Target node's column
            out_pos  : Which output position to configure
            msg_a_row: Output message target row A
            msg_a_col: Output message target column A
            msg_b_row: Output message target row B
            msg_b_col: Output message target column B
            msg_as_bc: Send message as a broadcast
            bc_decay : When broadcasting, how many steps to propagate
        """
        super().__init__(env, tgt_row, tgt_col)
        self.out_pos   = out_pos
        self.msg_a_row = msg_a_row
        self.msg_a_col = msg_a_col
        self.msg_b_row = msg_b_row
        self.msg_b_col = msg_b_col
        self.msg_as_bc = msg_as_bc
        self.bc_decay  = bc_decay

class SignalState(Base):
    """ Carries a signal value change between nodes """

    def __init__(
        self, env, tgt_row, tgt_col, broadcast, decay,
        src_row, src_col, src_pos, src_val,
    ):
        """ Initialise the message.

        Args:
            env      : SimPy environment
            tgt_row  : Target node's row
            tgt_col  : Target node's column
            broadcast: Whether to broadcast the message
            decay    : How many steps to allow a broadcast message to propagate
            src_row  : Source node's row
            src_col  : Source node's column
            src_pos  : Bit position from source
            src_val  : Bit value being transmitted
        """
        super().__init__(env, tgt_row, tgt_col, broadcast, decay)
        self.src_row = src_row
        self.src_col = src_col
        self.src_pos = src_pos
        self.src_val = src_val

    def __repr__(self):
        return (
            f"<SignalState - TR: {self.tgt_row}, TC: {self.tgt_col}, BC: "
            f"{self.broadcast}, BD: {self.decay}, SR: {self.src_row}, SC: "
            f"{self.src_col}, SP: {self.src_pos}, SV: {self.src_val}>"
        )

    def __str__(self):
        return self.__repr__()
