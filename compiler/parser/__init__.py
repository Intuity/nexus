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

import json
import logging
from pathlib import Path
import re

# If available, use Rich to colourise the output log
try:
    from rich.logging import RichHandler
    logging.basicConfig(
        level="NOTSET", format="%(message)s", datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
except ModuleNotFoundError:
    pass

log = logging.getLogger("parser")

from .model import Model
from .module import Module

class Parser:
    """ Parser for the JSON file output from Yosys """

    # Top-level section names
    CREATOR = "creator"
    MODULES = "modules"
    MODELS  = "models"

    # Regular expressions
    RGX_JSON_COMMENT = re.compile(r"(/[*][^*/]+[*]/)")
    RGX_CREATOR      = re.compile(r"^Yosys ([^\s]+) [(](.*?)[)]$")

    def __init__(self, path):
        """ Initialise the Parser instance.

        Args:
            path: Path to the file to read in
        """
        # Store the file path
        self.path = Path(path)

    def parse(self):
        """ Run the parser steps """
        # Read in the raw data
        raw_str = ""
        with open(self.path, "r") as fh: raw_str = fh.read()
        # Strip out comments in the form '/* ... */'
        clean_str = Parser.RGX_JSON_COMMENT.sub("", raw_str)
        # Convert JSON string into a dictionary
        data = json.loads(clean_str)
        # Digest each top-level section
        self.creator = self.parse_creator(data.get(Parser.CREATOR, None))
        self.modules = self.parse_modules(data.get(Parser.MODULES,   {}))
        self.models  = self.parse_models (data.get(Parser.MODELS,    {}))

    def parse_creator(self, raw):
        """ Parse the raw creator data string.

        Args:
            raw: The encoded creator information
        """
        version, build_info = Parser.RGX_CREATOR.match(raw).groups(0)
        log.info(f"Yosys Version: {version}, Build Info: {build_info}")

    def parse_modules(self, data):
        """ Parse the Yosys JSON module data into objects.

        Args:
            data: The dictionary parsed from Yosys JSON input
        """
        mods = []
        for key, desc in data.items():
            log.info(f"Detected module '{key}'")
            mods.append(Module(key, desc))
        return mods

    def parse_models(self, data):
        """ Parse the Yosys JSON model data into objects.

        Args:
            data: The dictionary parsed from Yosys JSON input
        """
        models = []
        for key, desc in data.items():
            log.info(f"Detected model '{key}'")
            models.append(Model(key, desc))
        return models
