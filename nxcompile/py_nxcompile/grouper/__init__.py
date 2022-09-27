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

from collections import defaultdict
from itertools import count
from statistics import mean
from random import choice

from .grouping import Grouping
from .partition import Partition

from nxcompile import nxsignal_type_t

def group_logic(module, limits):
    groups  = {}
    bkt_int = 20
    buckets = defaultdict(lambda: [])

    for flop in module.flops:
        # Define function to chase through logic & collect gates, flops, and ports
        # stopping at the first flop/port it finds on a given tree
        def chase(sig, ban_constants=False):
            if sig.is_type(nxsignal_type_t.WIRE):
                yield from chase(sig.inputs[0])
            elif sig.is_type(nxsignal_type_t.GATE):
                yield sig
                for input in sig.inputs:
                    yield from chase(input, ban_constants=True)
            elif sig.is_type(nxsignal_type_t.PORT):
                yield sig
            elif sig.is_type(nxsignal_type_t.FLOP):
                yield sig
            # Constants driving flops are acceptable (as they can create initial
            # conditions that update after 1 cycle), but they should have been
            # eliminated from all logic clouds
            elif ban_constants and sig.is_type(nxsignal_type_t.CONSTANT):
                raise Exception("Constant term found")
        # Search for ports, flops, and gates
        ports, flops, gates = [], [], []
        for entry in chase(flop.inputs[0]):
            {
                nxsignal_type_t.PORT: ports,
                nxsignal_type_t.FLOP: flops,
                nxsignal_type_t.GATE: gates,
            }[entry.type].append(entry)
        # Search for target ports
        tgt_ports = []
        for entry in flop.outputs:
            if entry.is_type(nxsignal_type_t.PORT):
                tgt_ports.append(entry)
        # Append the grouping
        group = Grouping(flop, ports, tgt_ports, flops, gates)
        groups[group.target.name] = group
        # Bucket the grouping based on complexity (number of gates)
        buckets[group.complexity // bkt_int].append(group)

    # Work out which other groups drive this one
    for group in groups.values():
        group.driven_by = {
            groups[x.name] for x in group.src_flops if groups[x.name] != group
        }

    # Work out which other groups this one drives
    for group in groups.values():
        group.drives_to = {
            x for x in groups.values() if group in x.driven_by if x != group
        }

    print(f"Formed {len(groups)} logic groupings:")
    ordered = sorted(groups.values(), key=lambda x: x.complexity)
    print(f" - Minimum Gates      : {ordered[0].complexity}")
    print(f" - Maximum Gates      : {ordered[-1].complexity}")
    print(f" - Average Gates      : {mean([x.complexity for x in ordered])}")
    print(f" - Minimum Flops+Ports: {min([len(x.src_ports)+len(x.src_flops) for x in ordered])}")
    print(f" - Maximum Flops+Ports: {max([len(x.src_ports)+len(x.src_flops) for x in ordered])}")
    print(f" - Average Flops+Ports: {mean([len(x.src_ports)+len(x.src_flops) for x in ordered])}")

    print()
    print(f"Gathered {len(buckets)} different buckets at interval {bkt_int}")
    for bkt_key, bucket in sorted(buckets.items(), key=lambda x: x[0]):
        bkt_min = bkt_key * bkt_int
        bkt_max = bkt_min + bkt_int - 1
        print(f" - {bkt_min:4d} to {bkt_max:4d}: {len(bucket)}")

    # # Look at how many groups each flop contributes to
    # contribs = []
    # for entry in groups:
    #     contribs.append(len([x for x in groups if entry.target.name in [y.name for y in x.src_flops]]))
    # contribs.sort()

    # print()
    # print(f"Minimum contributions of a flop: {contribs[0]}")
    # print(f"Maximum contributions of a flop: {contribs[-1]}")
    # print(f"Average contributions of a flop: {mean(contribs)}")

    # breakpoint()

    # Form partitions based on the logic
    partitions   = []
    tgt_flop_map = {}

    # Initial partition contains everything
    print()
    print("=== INITIAL PARTITIONING ===")
    print()
    partitions.append(Partition(0, limits, partitions, tgt_flop_map))
    for group in groups.values():
        partitions[0].add_group(group)
    partitions[0].aggregate()

    partition_limit = 100
    while len(partitions) < partition_limit:
        # Track whether all partitions fit within a node
        all_fit = True
        # Consider each partition in turn
        # NOTE: Copy list to avoid mutation during iteration
        for partition in partitions[:]:
            # Check if the partition already fits?
            if all(partition.fits().values()):
                continue
            # Is there more than one group in the partition
            if len(partition.groups) == 1:
                print(f"Partition {partition.idx} is too big but cannot be subdivided")
                continue
            # Flag that this partition doesn't fit
            all_fit = False
            # Split it in two
            partitions.append(Partition(len(partitions), limits, partitions, tgt_flop_map))
            part_a = partition
            part_b = partitions[-1]
            while len(part_a.groups) > len(part_b.groups):
                to_move = choice(part_a.groups)
                part_a.remove_group(to_move)
                part_b.add_group(to_move)
            part_a.aggregate()
            part_b.aggregate()
            # Refine the partition by minimising crossings
            def count_cross(grp, ptn):
                return (len(grp.drives_to.intersection(ptn.groups)) +
                        len(grp.driven_by.intersection(ptn.groups)))
            def count_all(ptn_0, ptn_1):
                return sum([count_cross(x, ptn_0) for x in ptn_1.groups])
            last_count = count_all(part_a, part_b)
            print(f"{part_a.id}, {part_b.id} pre-optimisation : {last_count:5d}")
            for opt_idx in count():
                # Determine crossing costs of each group
                crs_a2b, crs_b2a = [], []
                for group in part_a.groups:
                    crs_a2b.append((group, count_cross(group, part_b)))
                    assert group not in part_b.groups
                for group in part_b.groups:
                    crs_b2a.append((group, count_cross(group, part_a)))
                    assert group not in part_a.groups
                # Report
                crossings = count_all(part_a, part_b)
                assert crossings <= last_count
                last_count = crossings
                # Sort by crossing cost
                crs_a2b.sort(key=lambda x: x[1], reverse=True)
                crs_b2a.sort(key=lambda x: x[1], reverse=True)
                # Start swapping from most impactful to least impactful
                swaps = 0
                for (group_a, _), (group_b, _) in zip(crs_a2b, crs_b2a):
                    # Determine an up-to-date baseline cost
                    base_a2b = count_cross(group_a, part_b)
                    base_b2a = count_cross(group_b, part_a)
                    # Determine the swapped cost
                    swap_a2b = count_cross(group_a, part_a)
                    swap_b2a = count_cross(group_b, part_b)
                    # Do the two groups refer to each other?
                    # NOTE: Use '+2' because it changes 'drives_to' and 'driven_by'
                    swap_a2b += 2 if (group_b in group_a.drives_to) else 0
                    swap_b2a += 2 if (group_a in group_b.drives_to) else 0
                    # If not beneficial, swap back
                    benefit = (base_a2b + base_b2a) - (swap_a2b + swap_b2a)
                    if benefit > 0:
                        part_a.remove_group(group_a)
                        part_b.remove_group(group_b)
                        part_a.add_group(group_b)
                        part_b.add_group(group_a)
                        swaps += 1
                # If no swaps made, stop iterating
                if swaps == 0:
                    break
            # Log improvement
            print(f"{part_a.id}, {part_b.id} post-optimisation: {count_all(part_a, part_b):5d} ({opt_idx+1} passes)")
            # Update aggregations
            part_a.aggregate()
            part_b.aggregate()
            # Break out if reached the limit
            if len(partitions) >= partition_limit:
                break
        # If all partitions on this pass fit, then break out
        if all_fit:
            break

    # Print out a summary (ordered by maximum utilisation)
    print()
    print("=== AFTER PARTITIONING ===")
    print()
    num_fits = 0
    ord_util = sorted(partitions, key=lambda x: max(x.utilisation().values()), reverse=True)
    for partition in ord_util:
        print(partition.report())
        if all(partition.fits().values()):
            num_fits += 1
    print()
    print(f"{num_fits} partitions out of {len(partitions)} fit")
    print()

    # For violating partitions, attempt to relocate groups
    print("=== PARTITION RELAXATION ===")
    print()
    with_space = [x for x in ord_util if all(x.fits().values())]
    for src_part in ord_util:
        # If partition already fits, skip it
        if all(src_part.fits().values()):
            continue
        # Order the partition's groups by complexity
        print(f"Relocating logic from {src_part.id} ({len(src_part.groups)} groups)")
        for group in sorted(src_part.groups, key=lambda x: x.complexity, reverse=True):
            # Try relocating a group into another partition
            # NOTE: Only search through partitions with space
            for tgt_part in with_space:
                # Skip if source matches target, or target cannot fit group
                if tgt_part is src_part or not tgt_part.can_fit(group):
                    continue
                # Otherwise move the group
                # print(f"   + Moving group {group.id} from {src_part.id} to {tgt_part.id}")
                src_part.remove_group(group)
                tgt_part.add_group(group)
                tgt_part.aggregate()
                break
            # Re-aggregate source partition
            src_part.aggregate()
            # If partition now fits, break out
            if all(src_part.fits().values()):
                print(f" >> {src_part.id} now fits ({len(src_part.groups)} groups)")
                with_space.append(src_part)
                break
        # If got here, must never have achieved fit
        else:
            print(f" >> {src_part.id} still doesn't fit ({len(src_part.groups)} groups)")

    # Print out a summary (ordered by maximum utilisation)
    print()
    print("=== AFTER RELAXATION ===")
    print()
    num_fits = 0
    ord_util = sorted(partitions, key=lambda x: max(x.utilisation().values()), reverse=True)
    for partition in ord_util:
        print(partition.report())
        if all(partition.fits().values()):
            num_fits += 1
    print()
    print(f"{num_fits} partitions out of {len(partitions)} fit")
    print()

    # Attempt to merge partitions to free up some nodes
    print("=== PARTITION MERGING ===")
    print()
    for src_idx, src_part in enumerate(ord_util[::-1]):
        for tgt_part in ord_util[::-1][src_idx+1:]:
            if tgt_part.can_merge(src_part):
                print(f"Merging {src_part.id} with {tgt_part.id}")
                for group in src_part.groups[:]:
                    src_part.remove_group(group)
                    tgt_part.add_group(group)
                src_part.aggregate()
                tgt_part.aggregate()
                break

    # Print out a summary (ordered by maximum utilisation)
    print()
    print("=== AFTER MERGING ===")
    print()
    num_fits = 0
    ord_util = sorted(partitions, key=lambda x: max(x.utilisation().values()), reverse=True)
    for partition in ord_util:
        print(partition.report())
        if all(partition.fits().values()):
            num_fits += 1
    print()
    print(f"{num_fits} partitions out of {len(partitions)} fit")
    print()

    # Split partitions that are still violating
    print("=== PARTITION SPLITTING ===")
    print()
    empty_parts = [x for x in ord_util if not any(x.usage().values())]
    if len(empty_parts) > 0:
        for part in ord_util:
            # Skip partitions that already fit, or just have one group
            if all(part.fits().values()) or len(part.groups) == 1:
                continue
            # Check an empty partition exists
            if not empty_parts:
                break
            empty = empty_parts.pop(0)
            # Split groups evenly
            print(f"Splitting {part.id} into {empty.id}")
            while len(part.groups) > len(empty.groups):
                empty.add_group(part.groups[0])
                part.remove_group(part.groups[0])
            part.aggregate()
            empty.aggregate()

    # Eliminate any empty partitions
    partitions = [x for x in partitions if not x.empty]

    # Summarise partitioning
    print()
    print("=== PARTITIONING SUMMARY ===")
    print()
    num_fits  = 0
    num_over  = 0
    num_empty = 0
    ord_util  = sorted(partitions, key=lambda x: max(x.utilisation().values()), reverse=True)
    for partition in ord_util:
        print(partition.report())
        if not any(partition.usage().values()):
            num_empty += 1
        elif all(partition.fits().values()):
            num_fits += 1
        else:
            num_over += 1
    print()

    print(f">> {num_over:3d}/{len(partitions):3d} do not fit")
    print(f">> {num_fits:3d}/{len(partitions):3d} fit")
    print(f">> {num_empty:3d}/{len(partitions):3d} empty")
    print()

    return ord_util
