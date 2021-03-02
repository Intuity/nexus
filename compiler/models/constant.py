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

from .port import PortBit

class Constant(PortBit):
    """ Represents a constant value """

    CONST_ID = 0

    def __init__(self, value):
        """ Initialise the Constant instance.

        Args:
            value: Value carried by the constant - either 1 or 0
        """
        super().__init__(None, 0)
        assert isinstance(value, int)
        assert value in (0, 1)
        self.id    = Constant.issue_id()
        self.value = value

    @property
    def name(self): return f"CONST_{self.id}"

    @classmethod
    def issue_id(cls):
        issued = Constant.CONST_ID
        Constant.CONST_ID += 1
        return issued
