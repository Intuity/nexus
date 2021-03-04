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

from ..models.flop import Flop
from ..models.gate import Gate
from ..models.port import PortBit

log = logging.getLogger("compiler.prune")

def chase(bit):
    """ Chase a gate or bit through to the bits it drives.

    Args:
        bit: The bit to chase

    Returns: List of endpoints """
    endpoints = []
    if isinstance(bit, Gate):
        for tgt in bit.outputs:
            endpoints += chase(tgt)
    elif isinstance(bit, PortBit):
        endpoints.append(bit)
        for tgt in bit.targets:
            endpoints += chase(tgt)
    else:
        raise Exception(f"Can't chase {bit}")
    return endpoints

def prune(module):
    """ Prune unconnect logic from the module.

    Args:
        module: Input Module to clean up
    """
    while True:
        pruned = 0
        for child in module.children.values():
            endpoints = []
            if isinstance(child, Gate):
                for tgt in child.outputs[:]:
                    tgt_eps = chase(tgt)
                    if len(tgt_eps) == 0:
                        pruned += 1
                        child.outputs.remove(tgt)
            elif isinstance(child, Flop):
                for tgt in child.output[0].targets[:]:
                    tgt_eps = chase(tgt)
                    if len(tgt_eps) == 0:
                        pruned += 1
                        child.output[0].remove_target(tgt)
            else:
                raise Exception(f"Don't know how to prune {module}")
        log.debug(f"Pruned {pruned} connections")
        if pruned == 0: break
