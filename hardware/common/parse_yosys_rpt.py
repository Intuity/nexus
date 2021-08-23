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

import csv
import re
import sys

FINAL_SECTION = "=== design hierarchy ==="

TO_EXTRACT = {
    "Total"      : ["Number of cells:"],
    "LUTs"       : ["LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6"],
    "Muxes"      : ["MUXF7", "MUXF8"],
    "Block RAM"  : ["RAMB36E1"],
    "Logic Cells": ["Estimated number of LCs:"],
}

if __name__ == "__main__":
    # Read in the lines of the file
    lines = []
    with open(sys.argv[1], "r") as fh:
        lines += [x.strip() for x in fh.readlines()]
    # Filter out just the final section
    lines = lines[lines.index(FINAL_SECTION):]
    # Extract each metric
    metrics = {}
    for key, components in TO_EXTRACT.items():
        accum = 0
        for comp in components:
            for line in lines:
                matches = re.match(f"^{comp}\\s+([0-9]+)$", line)
                if matches:
                    accum += int(matches.group(1))
                    lines.remove(line)
                    break
        metrics[key] = accum
    # Produce a CSV
    with open(sys.argv[2], "w") as fh:
        writer = csv.writer(fh, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
        data   = list(metrics.items())
        writer.writerow([x[0] for x in data])
        writer.writerow([x[1] for x in data])
