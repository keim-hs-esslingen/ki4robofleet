#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script implements the sharing strategy
# The autonomous vehicles can transport more than one passenger and the requests
# have to be analyzed whether it makes sense to take a detour to pick another
# passenger or not.
# The SUMO Taxi functionality is used:
# https://sumo.dlr.de/docs/Simulation/Taxi.html
# =============================================================================


from types import new_class
from Tools.dotdict import DotDict

import copy

SPEED = 0.1
LATENESS = 2
COST_PER_DIST = 1
VALUE_PER_DIST = COST_PER_DIST * 10


def dist_to_cost(d):
    return int(d * COST_PER_DIST)


def dist_to_time(d, speed=SPEED):
    return int(d / speed)


def multi_step_distance(distances, arr):
    """
    returns full distance of a multi-step route
    arr contains list of indices of vertices
    """
    l = len(arr)
    d = 0
    from_idx = arr[0]
    for i in range(1, l):
        to_idx = arr[i]
        step = distances.dist_array[from_idx][to_idx]
        # print(f"{from_idx} to {to_idx}: {step}")
        d += step
        from_idx = to_idx
    return d


def shrink_multi_step_distance(distances, arr):
    """
    returns full distance of a multi-step route
    arr contains list of indices of vertices
    """
    d = 0
    from_idx = arr[0]
    compact = [from_idx]
    for to_idx in arr[1:]:
        if to_idx != from_idx:
            step = distances.dist_array[from_idx][to_idx]
            d += step
            compact += [to_idx]
            from_idx = to_idx
    return d, compact


def share_ride(requests, distances, i, j, speed=SPEED):
    """
    find potential for ride sharing of TWO requests
    requests are sorted by finish (NOT latest)
    if possible return a variant request containing i and j
    """
    req = requests[j]
    s1 = req.expected_start_time
    i1 = req.idx

    req_pre = requests[i]
    s2 = req_pre.expected_start_time
    l2 = req_pre.latest_finish_time
    i2 = req_pre.idx
    if l2 < s1:
        # req_pre ends before req starts
        return None
    elif s2 > s1:
        # full time overlap; s1, s2, f2, f1

        # default dist s1 -> f1
        default_dist = distances.dist_array[req.from_idx][req.to_idx]

        # dist s1 -> s2 -> f2 -> f1
        new_route = [req.from_idx, req_pre.from_idx, req_pre.to_idx, req.to_idx]
        reservation_order = [req.idx, req_pre.idx, req_pre.idx, req.idx]

        gross_dist, new_route = shrink_multi_step_distance(distances, new_route)
        detour_dist = gross_dist - default_dist
        detour_cost = dist_to_cost(detour_dist)
        added_value = req_pre.value - detour_cost

        tt = dist_to_time(gross_dist, speed)
        if req.expected_start_time + tt < req.latest_finish_time:
            r = copy.copy(req)
            r.value += added_value
            r.contains = [i1, i2]
            r.path = new_route
            r.reservations = reservation_order
            return r
    else:
        # partial time overlap s2 s1 f2 f1

        # default dist s1 -> f1
        dd1 = distances.dist_array[req.from_idx][req.to_idx]

        # default dist s2 -> f2
        dd2 = distances.dist_array[req_pre.from_idx][req_pre.to_idx]

        # dist s2 -> s1 -> f2 -> f1
        new_route = [req_pre.from_idx, req.from_idx, req_pre.to_idx, req.to_idx]
        reservation_order = [req_pre.idx, req.idx, req_pre.idx, req.idx]

        gross_dist, new_route = shrink_multi_step_distance(distances, new_route)
        detour_dist = gross_dist - dd1 - dd2
        detour_cost = dist_to_cost(detour_dist)
        added_value = req_pre.value - detour_cost

        detour1 = [req_pre.from_idx, req.from_idx, req_pre.to_idx]
        d1, _ = shrink_multi_step_distance(distances, detour1)
        tt1 = dist_to_time(d1, speed)

        detour2 = [req.from_idx, req_pre.to_idx, req.to_idx]
        d2, _ = shrink_multi_step_distance(distances, detour2)
        tt2 = dist_to_time(d2, speed)

        if (
            req.expected_start_time + tt2 < req.latest_finish_time
            and req_pre.expected_start_time + tt1 < req_pre.latest_finish_time
        ):
            r = copy.copy(req)
            r.expected_start_time = req_pre.expected_start_time
            r.from_idx = req_pre.from_idx
            r.value += added_value
            r.contains = [i1, i2]
            r.path = new_route
            r.reservations = reservation_order
            return r
    return None


def find_share_ride(requests, variants, distances, j, speed=SPEED):
    """
    find all sharing variants with request j

    variants: pass-by-reference
    """
    for i in range(j - 1, -1, -1):
        req_variant = share_ride(requests, distances, i, j, speed)
        if req_variant:
            req_variant.idx = len(requests) + len(variants)
            # print(f"{req_variant.idx} contains {req_variant.contains[0]}/{req_variant.contains[1]}")
            variants.append(req_variant)


def sharing(requests, distances, speed=SPEED):
    """
    find all sharing variants for all original requests
    return list of variants
    """
    l = len(requests)
    variants = []
    for j in range(l - 1, -1, -1):
        find_share_ride(requests, variants, distances, j, speed)
    return variants
