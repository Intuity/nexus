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

from ..io_common import BaseIO

class AXI4StreamIO(BaseIO):
    """ AXI4 stream interface """

    def __init__(self, dut, name, role):
        """ Initialise AXI4StreamIO.

        Args:
            dut : Pointer to the DUT boundary
            name: Name of the signal - acts as a prefix
            role: Role of this signal on the DUT boundary
        """
        super().__init__(dut, name, role, [
            "tvalid", "tdata", "tstrb", "tkeep", "tlast", "tid", "tdest",
            "tuser", "twakeup",
        ], [
            "tready",
        ])
