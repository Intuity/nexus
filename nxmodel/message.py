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

    def __init__(self, env, row, col):
        """ Initialise Message instance.

        Args:
            env: SimPy environment
            row: Message recipient node's row
            col: Message recipient node's column
        """
        super().__init__(env)
        assert isinstance(row, int) and row >= 0
        assert isinstance(col, int) and col >= 0
        self.row      = row
        self.col      = col
        self.tracking = []

    @property
    def target(self): return self.row, self.col

    def copy(self):
        copied          = copy.copy(self)
        copied.tracking = self.tracking[:]
        return copied

class LoadInstruction(Message):
    """ Load an instruction into a core """

    def __init__(self, env, row, col, instr):
        """ Initialise the message.

        Args:
            env  : SimPy environment
            row  : Message recipient node's row
            col  : Message recipient node's column
            instr: The instruction to load
        """
        super().__init__(env, row, col)
        self.instr = instr


class ConfigureOutput(Message):
    """ Configure output messaging """

    def __init__(
        self, env, row, col, src_idx, tgt_row, tgt_col, tgt_idx, tgt_seq
    ):
        """ Initialise the message.

        Args:
            env    : SimPy environment
            row    : Message recipient node's row
            col    : Message recipient node's column
            src_idx: Output index to append a mapping for
            tgt_row: Target node's row for signal state messages
            tgt_col: Target node's column for signal state messages
            tgt_idx: Target node's input index for signal state messages
            tgt_seq: Whether the target node's input is sequential
        """
        super().__init__(env, row, col)
        self.src_idx = src_idx
        self.tgt_row = tgt_row
        self.tgt_col = tgt_col
        self.tgt_idx = tgt_idx
        self.tgt_seq = tgt_seq

class SignalState(Message):
    """ Carries a signal value change between nodes """

    def __init__(self, env, row, col, index, value, is_seq):
        """ Initialise the message.

        Args:
            env   : SimPy environment
            row   : Message recipient node's row
            col   : Message recipient node's column
            index : Input index
            value : Value carried
            is_seq: Treat value as sequential
        """
        super().__init__(env, row, col)
        self.index  = index
        self.value  = value
        self.is_seq = is_seq

    @property
    def source(self): return self.src_row, self.src_col

    def __repr__(self):
        return (
            f"<SignalState - R: {self.row}, C: {self.col}, I: {self.index}, "
            f"V: {self.value}, SQ: {self.is_seq}>"
        )

    def __str__(self):
        return self.__repr__()
