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

from .signal import Signal

class Constant(Signal):
    """ Represents a constant value """

    def __init__(self, value, width):
        """ Initialise the Constant instance.

        Args:
            value: The value of the constant (as an integer)
            width: Width of the constant
        """
        assert isinstance(value, int)
        super().__init__(f"{value:0{width}b}", width, [])
        self.value = value
