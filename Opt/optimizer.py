#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides tools for route optimization
# =============================================================================


from Tools.dotdict import DotDict
from Tools.logger import log
from Moving.request import Request, dist_to_cost


def value_cost(start_idx, requests, distances, values, j):
    """
    returns value of request
        plus value of predecessor
        minus travel cost from target of predecessor to start of req
    """
    req = requests[j - 1]
    pre_value = 0
    if req.pre > -1:
        req_pre = requests[req.pre]
        cost = dist_to_cost(distances.dist_array[req_pre.to_idx][req.from_idx])
        pre_value = values[req.pre + 1] - cost
    else:
        cost = dist_to_cost(distances.dist_array[start_idx][req.from_idx])
        pre_value = -cost
    # do not return negative cost
    return max(1, req.value + pre_value)


def predecessor(requests, distances, j, time_safety_factor):
    """
    find predecessor of the request with index j
    consider time to travel from target of predecessor to start of req
    store predecessor index in requests
    """

    req = requests[j]
    req.pre = -1
    for i in range(j - 1, -1, -1):
        req_pre = requests[i]
        from_idx = req_pre.to_idx  # target of predecessor
        to_idx = req.from_idx  # start of request
        travel_time = distances.time_array[from_idx][to_idx]
        if (
            req.expected_start_time
            > req_pre.expected_finish_time + travel_time * time_safety_factor
        ):
            req.pre = i
            return


def find_opt(start_idx, requests, distances, values, j):
    """
    returns list of indices of fullfilled requests
    """
    indices = []
    value = 0
    vc = value_cost(start_idx, requests, distances, values, j)
    if j == 0:
        pass
    elif vc > values[j - 1]:
        value += vc
        indices += [j - 1]
        (i, v) = find_opt(
            start_idx, requests, distances, values, requests[j - 1].pre + 1
        )
        indices += i
        value += v
    else:
        (i, v) = find_opt(start_idx, requests, distances, values, j - 1)
        indices += i
        value += v

    return (indices, value)


def one_optimal_route(start_idx, requests, distances, time_safety_factor=1.2):
    """
    find one optimal route between requests
    """
    n = len(requests)

    for j in range(n - 1, -1, -1):
        predecessor(requests, distances, j, time_safety_factor)

    values = [0 for _ in range(n + 1)]
    for j in range(1, n + 1):
        v = value_cost(start_idx, requests, distances, values, j)
        values[j] = max(v, values[j - 1])

    (indices, value) = find_opt(start_idx, requests, distances, values, n)

    fullfilled = []
    reservations = []
    for j in indices:
        req: Request = requests[j]
        # if the fullfilled request is a shared ride:
        #  append the original requests to fullfilled
        if req.contains:
            if req.idx not in fullfilled:
                fullfilled.append(req.idx)
            reqidx0 = req.contains[0]
            reqidx1 = req.contains[1]
            if reqidx0 not in fullfilled and reqidx1 not in fullfilled:
                fullfilled.append(reqidx0)
                fullfilled.append(reqidx1)
                reservations.append(req.reservations)
            elif reqidx0 not in fullfilled:
                fullfilled.append(reqidx0)
                reservations.append([reqidx0, reqidx0])
            elif reqidx1 not in fullfilled:
                fullfilled.append(reqidx1)
                reservations.append([reqidx1, reqidx1])
        elif req.idx not in fullfilled:
            # TWO Entries: pickup and drop
            fullfilled.append(req.idx)
            reservations.append([req.idx, req.idx])
        log(
            f"{req.idx:3d} {req.submit_time:4d} {req.latest_finish_time:4d} {reservations}"
        )

    # req_indices = [r.idx for r in requests]
    log(f"{len(requests):} requests: {len(fullfilled)} fullfilled")

    # reversal of list: early reservations first
    return (fullfilled, value, list(reversed(reservations)))


def routing_with_variants(
    start_idx, requests, variants, distances, time_safety_factor=1.2
):
    """
    return list of routes
    each route has:
    - fullfilled: list of request IDs
    """
    routes = []

    # indices of original requests
    no_variants = [r.idx for r in requests]

    # rv: list of requests and request variants
    rv = requests.copy() + variants
    rv = sorted(rv, key=lambda r: r.latest_finish_time)

    while len(rv):
        o = DotDict()
        (fullfilled, o.sum, o.reservations) = one_optimal_route(
            start_idx, rv, distances, time_safety_factor
        )
        # store only original requests, not variants
        o.fullfilled = [i for i in fullfilled if i in no_variants]
        routes.append(o)
        next_rv = []
        # clear list of open requests
        # rm all requests that are fullfilled
        for r in rv:
            if r.idx in fullfilled:
                continue
            if r.contains:
                if r.contains[0] in fullfilled:
                    continue
                if r.contains[1] in fullfilled:
                    continue
            next_rv.append(r)
        rv = next_rv
    return routes
