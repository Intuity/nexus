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

from random import choice, randint
from typing import List, Tuple, Optional

from nxconstants import (OutputLookup, OutputMapping, MAX_ROW_COUNT,
                         MAX_COLUMN_COUNT, NodeID)

def gen_output_mappings(
    outputs  : int,
    inputs   : int,
    rows     : int = MAX_ROW_COUNT,
    columns  : int = MAX_COLUMN_COUNT,
    base_off : int = 0,
    min_tgts : int = 1,
    max_tgts : int = 1,
    exclude  : Optional[NodeID] = None,
) -> Tuple[List[OutputLookup], List[List[OutputMapping]]]:
    """
    Generate random output mappings for a node, returning the mappings for each
    output along with the lookup table.

    Args:
        outputs : How many outputs to generate
        inputs  : Number of inputs on target nodes
        base_off: Base placement address for mappings and lookup
        min_tgts: Minimum number of targets to generate for each output
        max_tgts: Maximum number of targets to generate for each output
        exclude : Optionally exclude a node from targets

    Returns: Mappings and lookup table
    """
    # Generate mappings for each active output
    used    = []
    targets = []
    offsets = [base_off+outputs]
    for index in range(outputs):
        targets.append([])
        num_tgts = randint(min_tgts, max_tgts)
        # Choose a number of unique targets
        for _ in range(num_tgts):
            tgt_row, tgt_col, tgt_idx = 0, 0, 0
            while True:
                tgt_row = randint(0, rows-1)
                tgt_col = randint(0, columns-1)
                tgt_idx = randint(0, inputs-1)
                tgt_seq = choice((0, 1))
                # If this targets an excluded node, skip
                if exclude and exclude.row == tgt_row and exclude.column == tgt_col:
                    continue
                # Check if this target is unique
                if (tgt_row, tgt_col, tgt_idx) not in used:
                    used.append((tgt_row, tgt_col, tgt_idx))
                    break
            targets[index].append(OutputMapping(
                row   =tgt_row,
                column=tgt_col,
                index =tgt_idx,
                is_seq=tgt_seq,
            ))
        # Accumulate offsets
        offsets.append(offsets[-1]+num_tgts)
    # Generate lookups
    lookups = [
        OutputLookup(active=(len(m) > 0), start=o, stop=(o+len(m)-1))
        for m, o in zip(targets, offsets)
    ]
    # Return lookups and mappings
    return lookups, targets
