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

import click

from .parser import Parser

@click.command()
@click.argument("input")
def main(input):
    """ Compiles Yosys JSON export into a Nexus instruction schedule

    Arguments:

        input: Path to the Yosys JSON export
    """
    # Run the parse step on the Yosys JSON input
    parser = Parser(input)
    parser.parse()
    print(parser.modules[0])

if __name__ == "__main__":
    main()
