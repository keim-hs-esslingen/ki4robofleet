#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides the POI_Manager- Class to store and manage
# Points of Interest
# =============================================================================


from Tools.logger import dlog, elog
import random
from typing import List
import json
import codecs

import xml.etree.ElementTree as ET

from Tools.dotdict import DotDict
from Net.point_of_interest import Point_of_Interest, PARKING_POI


def near(f1: float, f2: float) -> bool:
    return abs(f1 - f2) < 0.1


class POI_Manager:
    def __init__(self):
        self.poi_arr = []
        self.valid_edges = []
        self.edge_dict = {}
        self.average_speed = 1

    def get_speed(self):
        return self.average_speed

    def __iter__(self):
        return iter(self.edge_dict)

    def get_poi_edges(self):
        return [poi.edge_id for poi in self.poi_arr]

    def add(self, poi: Point_of_Interest):
        self.poi_arr.append(poi)

    def add_lane_to_edge(self, edge_id, lane_id):
        if edge_id not in self.edge_dict:
            self.edge_dict[edge_id] = [lane_id]
        else:
            self.edge_dict[edge_id].append(lane_id)

    def write_poi_types(self):
        lst = [poi.poi_type for poi in self.poi_arr]
        categories = set()
        poi_type_set = set(lst)
        for poi_type in poi_type_set:
            if "." in poi_type:
                parts = poi_type.split(".")
                categories.add(parts[0])
            else:
                categories.add(poi_type)

        obj = {
            "categories": sorted(list(categories)),
            "types": sorted(list(poi_type_set)),
        }
        codec = codecs.open("poi_types.json", "w", encoding="utf-8")
        json.dump(obj, codec, indent=4)

    def random_poi(self):
        return random.choice(self.poi_arr)

    def parking_POI(self) -> List[Point_of_Interest]:
        return [poi for poi in self.poi_arr if poi.poi_type == PARKING_POI]

    def pre_parking(self, n):
        filtered = [poi for poi in self.poi_arr if poi.poi_type == PARKING_POI]
        num_parking = len(filtered)
        # if there is no parking left use other pois
        if num_parking == 0:
            filtered = self.poi_arr
            num_parking = len(filtered)
        if n >= num_parking:
            idx = n % num_parking
        else:
            idx = n
        return filtered[idx]

    def find_poi(self, edge, pos):
        for poi in self.poi_arr:
            if poi.edge_id == edge:
                if near(poi.pos, pos):
                    return poi
        elog(f"do not find POI at edge {edge} {pos}")
        return None

    def non_parking(self):
        filtered = [poi for poi in self.poi_arr if poi.poi_type != PARKING_POI]
        return random.choice(filtered)

    def random_poi_by_type(self, poi_type=PARKING_POI):
        filtered = [poi for poi in self.poi_arr if poi.poi_type == poi_type]
        if filtered:
            return random.choice(filtered)
        return random.choice(self.poi_arr)

    def poi_by_walk(self):
        return [poi for poi in self.poi_arr if poi.walk_lane != None]

    def random_poi_by_walk(self):
        filtered = [poi for poi in self.poi_arr if poi.walk_lane != None]
        if filtered:
            return random.choice(filtered)
        return random.choice(self.poi_arr)

    def random_poi_by_walk_and_type(self, poi_type):
        filtered = [
            poi
            for poi in self.poi_arr
            if poi.walk_lane != None and poi_type in poi.poi_type
        ]
        if filtered:
            return random.choice(filtered)
        return random.choice(self.poi_arr)

    def clean(self, valid_edges):
        filtered = [poi for poi in self.poi_arr if poi.edge_id in valid_edges]
        self.poi_arr = filtered
        self.valid_edges = valid_edges

    def edge_is_valid(self, edge_id):
        return edge_id in self.valid_edges

    def dist_matrix(self, traci, poi_arr=None):
        """
        calculate:
        - distances
        - times
        - edges/routes
        between POIs
        """
        distances = 0
        travel_times = 0

        if poi_arr:
            self.poi_arr = poi_arr
        length = len(self.poi_arr)
        dist_array = [[0 for i in range(length)] for j in range(length)]
        time_array = [[0 for i in range(length)] for j in range(length)]
        edges_array = [[0 for i in range(length)] for j in range(length)]

        len_of_poi = len(self.poi_arr)
        for i, from_poi in enumerate(self.poi_arr):
            continue
            sum = 0
            if i % 10 == 0:
                dlog(f"distance {i:4d}:{len_of_poi}")
            assert from_poi.idx == i
            for j, to_poi in enumerate(self.poi_arr):
                assert to_poi.idx == j
                if from_poi != to_poi:
                    if dist_array[j][i] > 0:
                        dist_array[i][j] = dist_array[j][i]
                        time_array[i][j] = time_array[j][i]
                        edges_array[i][j] = edges_array[j][i]
                    else:
                        stage_to = traci.simulation.findRoute(
                            from_poi.edge_id, to_poi.edge_id
                        )
                        if stage_to and len(stage_to.edges):
                            distances += stage_to.length
                            travel_times += stage_to.travelTime
                            dist_array[i][j] = stage_to.length
                            time_array[i][j] = stage_to.travelTime
                            edges_array[i][j] = stage_to.edges
                            sum += stage_to.length
                        else:
                            # this should not happen because sumo_reader cleaned roads
                            # and removed non-valid POIS
                            elog(
                                f"no path from poi {from_poi.poi_id} to {to_poi.poi_id}"
                            )

        obj = DotDict()
        obj.dist_array = dist_array
        obj.time_array = time_array
        obj.edges_array = edges_array
        self.average_speed = 0
        return obj

    def same_edges(self):
        edges = {}
        for from_poi in self.poi_arr:
            for to_poi in self.poi_arr:
                if from_poi != to_poi:
                    if from_poi.edge_id == to_poi.edge_id:
                        if from_poi.edge_id not in edges:
                            edges[from_poi.edge_id] = [from_poi, to_poi]
                        else:
                            if from_poi not in edges[from_poi.edge_id]:
                                edges[from_poi.edge_id].append(from_poi)
                            if to_poi not in edges[from_poi.edge_id]:
                                edges[from_poi.edge_id].append(to_poi)

        return edges

    def allow(self, traci, allowed_types):
        for poi in self.poi_arr:
            if poi.edge_id in self.edge_dict:
                if poi.edge_id == "426912946#1":
                    print("Check")
                for lane_id in self.edge_dict[poi.edge_id]:
                    traci.lane.setAllowed(lane_id, allowed_types)

    def allow_path(self, traci, edges, allowed_types):
        for edge_id in edges:
            for lane_id in self.edge_dict[edge_id]:
                traci.lane.setAllowed(lane_id, allowed_types)
                # allowed = traci.lane.getAllowed(lane_id)
                # print("allow lane", lane_id, allowed)
