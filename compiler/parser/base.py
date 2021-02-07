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

class Base:
    """ Base model """

    def __init__(self, name):
        """ Initialise the Base instance.

        Args:
            name: Name of the model
        """
        assert isinstance(name, str)
        self.name       = name
        self.attributes = {}

    @property
    def safe_name(self):
        return self.name.translate(str.maketrans({
            "[" : "_", "]" : "_", ":" : "_", "\\": "_",
        }))

    def set_attribute(self, key, value):
        """ Add an arbitrary attribute to the signal.

        Args:
            key  : Key of the attribute (must be a string)
            value: Value of the attribute (any type)
        """
        assert isinstance(key, str)
        self.attributes[key] = value
