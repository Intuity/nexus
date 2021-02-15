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

class Constant:
    """ Represents a constant bit value """

    def __init__(self, value):
        """ Initialise the Constant instance.

        Args:
            value: Value of the constant (either 0 or 1)
        """
        assert isinstance(value, int) and value in (0, 1)
        self.value = value
