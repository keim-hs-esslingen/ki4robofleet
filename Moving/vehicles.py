#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: January 2021
# License: MIT License
# =============================================================================
# This Script provides the Vehicle- Class to store and handle Vehicle- Information
# See also: https://sumo.dlr.de/pydoc/traci._vehicle.html
# =============================================================================

import os
import time

from enum import IntEnum
from Tools.check_sumo import sumo_available
from Tools.logger import log, elog, dlog

sumo_available()
import traci  # noqa


STOP_DURATION = 50

# VEHICLE COLORS
COLOR_FULFILLING = (245, 215, 66)
COLOR_WITH_PASSENGER = (252, 139, 10)
COLOR_PARKING = (66, 209, 245)
COLOR_STOPPED = (245, 0, 0)


print("VEHICLE # Loading", __file__, time.ctime(os.path.getmtime(__file__)))


class ModeType(IntEnum):
    free_driving = 0  # blue
    to_passenger = 1  # red
    with_passenger = 2  # green


class Vehicle:
    def __init__(self, vehID: str):
        self.vehID = vehID
        self.edge = None
        self.dist = 0
        self.pos = 0

    def update(self):
        try:
            edge = traci.vehicle.getRoadID(self.vehID)
            is_stopped = traci.vehicle.isStopped(self.vehID)
            if edge != "" and not ":" in edge:
                self.edge = edge
                if not is_stopped:
                    # last_lane_id = traci.vehicle.getLaneID(self.pid)
                    self.pos = traci.vehicle.getLanePosition(self.vehID)
                    self.dist = max(0, traci.vehicle.getDistance(self.vehID) / 1000)

        except Exception as e:
            elog(f"monitor error {e}")
        return None
