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

from enum import IntEnum

class IORole(IntEnum):
    """ Role that a particular bus is performing (determines signal suffix) """
    INITIATOR = 0
    RESPONDER = 1

class BaseIO:
    """ Base I/O wrapper class """

    def __init__(self, dut, name, role, init_sigs, resp_sigs):
        """ Initialise BaseIO.

        Args:
            dut      : Pointer to the DUT boundary
            name     : Name of the signal - acts as a prefix
            role     : Role of this signal on the DUT boundary
            init_sigs: Signals driven by the initiator
            resp_sigs: Signals driven by the responder
        """
        # Sanity checks
        assert role in IORole, f"Role {role} is not recognised"
        assert isinstance(init_sigs, list), "Initiator signals are not a list"
        assert isinstance(resp_sigs, list), "Responder signals are not a list"
        # Hold onto attributes
        self.__dut       = dut
        self.__name      = name
        self.__role      = role
        self.__init_sigs = init_sigs[:]
        self.__resp_sigs = resp_sigs[:]
        # Pickup attributes
        self.__initiators, self.__responders = [], []
        for comp in self.__init_sigs:
            sig  = f"{self.__name}_{comp}_"
            sig += "o" if self.__role == IORole.INITIATOR else "i"
            if not hasattr(self.__dut, sig): continue
            sig_ptr = getattr(self.__dut, sig)
            self.__initiators.append(sig_ptr)
            setattr(self, comp, sig_ptr)
        for comp in self.__resp_sigs:
            sig  = f"{self.__name}_{comp}_"
            sig += "i" if self.__role == IORole.INITIATOR else "o"
            if not hasattr(self.__dut, sig): continue
            sig_ptr = getattr(self.__dut, sig)
            self.__responders.append(sig_ptr)
            setattr(self, comp, sig_ptr)

    def initialise(self, role):
        """ Initialise signals according to the active role """
        for sig in (
            self.__initiators if role == IORole.INITIATOR else self.__responders
        ):
            sig <= 0
