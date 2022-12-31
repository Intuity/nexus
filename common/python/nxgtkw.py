from collections import defaultdict
import json
import re
import sys

data = {}
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)

# Extract port listings
ports = sum([x["ports"] for x in data["nodes"]], [])

# Build GTKWave bundles
lookup = {}
for idx_set, signals in enumerate(ports):
    for idx_bit, bit in enumerate(signals):
        lookup[bit] = f"({7-idx_bit})dut.R15C0I{idx_set}[7:0]"

# Group up signals
rgx_signal = re.compile(r"^([\w]+)_([0-9]+)$")
grouped    = defaultdict(list)
for signal, source in lookup.items():
    if match := rgx_signal.match(signal):
        grouped[match.group(1)].append((int(match.group(2)), source))
    else:
        grouped[signal].append((0, source))

# Sort groups in ascending order
for key, group in grouped.items():
    grouped[key] = sorted(group, key=lambda x: x[0])

# Write out signal mappings
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    for key, signals in grouped.items():
        fh.write(f"#{'{'}{key}{'}'} {' '.join([x[1] for x in signals])}\n")
