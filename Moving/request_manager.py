#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides the Class Request_Manager to manage the
# customer (passenger) requests
# =============================================================================

import os
import datetime
from Tools.logger import elog
from Moving.request import Request
from termcolor import colored

MINUTE = 60
HOUR = MINUTE * 60


def idx_append(ele, lst):
    if ele in lst:
        return lst.index(ele)
    lst.append(ele)
    return len(lst) - 1


class Request_Manager:
    def __init__(self, sumo_public={}):
        self.requests = None
        self.sumo_public = sumo_public
        self.t_wait = 0
        self.t_drive = 0
        self.d_full_mileage = 0
        self.time_safety_factor = 1
        self.d_pass = 0
        self.requests = []
        Request.manager = self

    def set_requests(self, requests):
        self.t_wait = 0
        self.t_drive = 0
        self.d_full_mileage = 0
        self.d_pass = 0
        self.requests = requests

    def get_result(self):
        num_fullfilled = sum(1 for r in self.requests if r.exit_time > 0)
        maxTime = 0
        for r in self.requests:
            if r.exit_time > maxTime:
                maxTime = r.exit_time

        d_empty = self.d_full_mileage - self.d_pass
        return {
            "fullfilled requests": num_fullfilled,
            "simulation_exit_time (sec)": maxTime,
            "t_wait (sec)": self.t_wait,
            "t_drive (sec)": self.t_drive,
            "d_full_mileage (km)": round(self.d_full_mileage, 3),
            "d_pass (km)": round(self.d_pass, 3),
            "d_empty (km)": round(d_empty, 3),
        }

    def requests_finished(self, d_full_mileage):
        self.d_full_mileage = d_full_mileage

    def request_finished(self, t_wait, t_drive, d_full_mileage, d_pass):
        self.t_wait += t_wait  # time the passenger waited
        self.t_drive += t_drive  # time the passenger was in car
        self.d_pass += d_pass  # add distance of vehicle driving with passenger

        d_empty = self.d_pass - d_full_mileage
        num_fullfilled = sum(1 for r in self.requests if r.exit_time > 0)

        self.sumo_public[
            "fullfilled requests"
        ] = f"{num_fullfilled}/{len(self.requests)}"
        self.sumo_public[
            "passenger waited"
        ] = f"{str(datetime.timedelta(seconds=t_wait))} h:m:s"
        self.sumo_public[
            "passenger in car"
        ] = f"{str(datetime.timedelta(seconds=t_drive))} h:m:s"
        self.sumo_public["distance full mileage"] = f"{d_full_mileage:.1f} km"
        self.sumo_public["distance with passenger"] = f"{self.d_pass:.1f} km"
        self.sumo_public["distance without passenger"] = f"{d_empty:.1f} km"
