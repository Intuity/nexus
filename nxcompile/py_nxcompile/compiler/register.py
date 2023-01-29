# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

class Register:

    def __init__(self, index, width=8):
        self.index    = index
        self.elements = [None] * width
        self.age      = 0
        self.active   = False
        self.novel    = False

    def __getitem__(self, key):
        return self.elements[key]

    def __setitem__(self, key, val):
        self.elements[key]

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def aging(self):
        self.age = (self.age + 1) if self.active else 0

    def __iter__(self):
        return self.elements
