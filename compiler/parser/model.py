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

import logging

log = logging.getLogger("parser.model")

class Model:
    """ Representation of an AIG model from Yosys JSON """

    def __init__(self, name, raw):
        """ Initialise the Model instance.

        Args:
            name: Name of the model
            raw : The raw list from the Yosys JSON output
        """
        assert isinstance(name, str)
        assert isinstance(raw,  list)
        self.name = name
        self.raw  = raw
