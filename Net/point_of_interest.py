#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script provides the Point_of_Interest- Class to store and
# handle Point_of_Interest- Information
# =============================================================================

from Tools.dotdict import DotDict

PARKING_POI = "parking"


class Point_of_Interest:
    def __init__(self, pid, eid):
        self.poi_id = pid
        self.edge_id = eid
        self.park_id = None
        self.streetname = None
        self.poi_type = None
        self.color = [255,0,0]
        self.length = 0
        self.pos = 0
        self.road = None
        self.walk_lane = None
        self.road_lane = None
        self.valid = True
        self.idx = None

    def dd(self):
        d = DotDict()
        d.edge = self.edge_id
        d.type = self.poi_type
        d.pos = self.pos
        d.id = self.poi_id
        return d

    def __str__(self):
        return f"{self.poi_id}: {self.poi_type}: {self.edge_id} : {self.color}, {self.pos}"
