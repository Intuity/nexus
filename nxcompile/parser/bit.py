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

from .constant import Constant

class Bit:
    """ Represents a single bit """

    def __init__(self, index, parent):
        """ Initialise the Bit instance.

        Args:
            index : Bit index within the parent vector
            parent: Parent node
        """
        self.index     = index
        self.parent    = parent
        self.__driver  = None
        self.__targets = []

    @property
    def driver(self):
        return self.__driver

    @driver.setter
    def driver(self, drvr):
        assert type(drvr) in (Bit, Constant)
        assert self.__driver == None
        self.__driver = drvr

    @property
    def targets(self):
        return self.__targets[:]

    def add_target(self, tgt):
        assert isinstance(tgt, Bit)
        self.__targets.append(tgt)
