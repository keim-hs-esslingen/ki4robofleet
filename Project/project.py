#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script provides the Class Project to set up the Simulation
# =============================================================================

from Moving import request
from Moving.request_manager import Request_Manager
from Tools.dotdict import DotDict
import os
import atexit
import xml.etree.ElementTree as ET
from typing import List

from random import randint, choice

from Tools.pickle_io import read_pickle, write_pickle
from Tools.logger import log, elog, dlog

from Net.point_of_interest import PARKING_POI, Point_of_Interest
from Moving.request import Request
from Project.check import (
    check_requests,
    shared_strategy,
    simple_strategy,
    look_ahead_strategy,
)
from Project.project_data import ProjectConfigData

from Net.poi_manager import POI_Manager
from Project.sumo_reader import SumoReader

from Opt.optimizer import routing_with_variants
from Opt.sharing import sharing

from Tools.check_sumo import sumo_available

sumo_available()
from sumolib import checkBinary  # noqa
import traci  # noqa


def starting_POI(poi_mgr: POI_Manager, no_of_poi: int) -> List[Point_of_Interest]:
    walk_poi = poi_mgr.poi_by_walk()
    parking = [poi for poi in walk_poi if poi.poi_type == PARKING_POI]
    valid_POIs = [poi for poi in walk_poi if poi.poi_type != PARKING_POI]

    poi_arr = []
    for _ in range(no_of_poi):
        poi: Point_of_Interest = choice(valid_POIs)
        if poi not in poi_arr:
            poi_arr.append(poi)

    all_poi = poi_arr + parking
    for i, poi in enumerate(all_poi):
        poi.idx = i
    return all_poi


STAY_TIME = 10


def passenger_request(poi_arr, distances, epoch_duration) -> Request:
    valid_POIs = [poi for poi in poi_arr if poi.poi_type != PARKING_POI]
    return random_request(valid_POIs, distances, epoch_duration)


def random_request(poi_arr, distances, epoch_duration) -> Request:
    from_poi = choice(poi_arr)
    to_poi = choice(poi_arr)
    while to_poi == from_poi:
        to_poi = choice(poi_arr)

    from_idx = from_poi.idx
    to_idx = to_poi.idx

    calculated_distance = distances.dist_array[from_idx][to_idx]
    calculated_time = distances.time_array[from_idx][to_idx]

    submit_time = randint(0, epoch_duration - STAY_TIME)
    request = Request(
        from_poi,
        to_poi,
        submit_time=submit_time,
        calculated_distance=calculated_distance,
        calculated_time=calculated_time,
    )
    request.from_idx = from_idx
    request.to_idx = to_idx
    request.measure = True
    return request


NO_OF_POI = 5
NO_OF_TRIPS = 10
MINUTE = 60
HOUR = MINUTE * 60


class Project:
    def __init__(self):
        self.traci_started = False
        self.data: ProjectConfigData = None

    def load(self, config: ProjectConfigData):
        self.data: ProjectConfigData = read_pickle(config.project_file, config)

        for att, value in config.__dict__.items():
            if value != None:
                self.data.__dict__[att] = value
                dlog(f"using {att} = {value}")

        self.data.realistic_time = 1.0

        if self.data.requests == None or len(self.data.requests) == 0:
            if config.requests_file and os.path.exists(config.requests_file):
                self.data.requests_file = config.requests_file
                self.read_requests_xml_file()
            else:
                self.select_poi_and_create_requests()
        else:
            elog(
                f"Using requests, POI, parking and distances from {config.project_file}"
            )

    def init_poi_manager(self):
        assert self.data.clean_edge != None
        self.init_sumo()
        poi_mgr = POI_Manager()
        reader = SumoReader(poi_mgr)
        reader.read_config(self.data.sumo_config_file)
        
        # clean_roads takes a lot of time, therefore it should be considered to skip this method
        reader.clean_roads(traci, self.data.clean_edge)
        
        return poi_mgr

    def select_poi_and_create_requests(self):
        """
        create new requests from new POI-list
        calculate distances/times between POIs
        """
        poi_mgr = self.init_poi_manager()
        self.data.poi = starting_POI(poi_mgr=poi_mgr, no_of_poi=self.data.no_of_poi)
        self.data.parking = [
            poi for poi in self.data.poi if poi.poi_type == PARKING_POI
        ]

        self.data.distances = poi_mgr.dist_matrix(traci, poi_arr=self.data.poi)
        self.data.speed = poi_mgr.get_speed()

        unsorted = []
        for _ in range(self.data.no_of_trips):
            unsorted.append(
                passenger_request(
                    poi_arr=self.data.poi,
                    distances=self.data.distances,
                    epoch_duration=HOUR,
                )
            )
        self.data.requests = sorted(
            unsorted, key=lambda r: r.submit_time, reverse=False
        )

        log(f"Project saving {self.data.project_file} ")
        write_pickle(self.data.project_file, self.data)

    def read_requests_xml_file(self, start=0):
        """
        read requests from XML
        create list of used POI
        calculate distances/times between POIs
        """

        unsorted = []
        poi_mgr = self.init_poi_manager()
        parking = poi_mgr.parking_POI()
        poi_arr = []
        dlog(f"read requests {self.data.requests_file}")
        netTree = ET.parse(self.data.requests_file)
        netRoot = netTree.getroot()
        requests = netRoot.findall("request")

        checked_requests = []
        genericPoiIdCounter = 0

        # iterate XML-requests
        for req in requests:
     
            from_poi = None
            to_poi = None
            # here we check if the current customer request is assigned to a certain POI 
            if req.attrib.get("fromPOI"):
                from_poi = poi_mgr.find_poi(
                    req.attrib.get("fromEdge"), float(req.attrib.get("fromEdgePosition"))
                )
                to_poi = poi_mgr.find_poi(
                    req.attrib.get("toEdge"), float(req.attrib.get("toEdgePosition"))
                )

            # if the current customer request is not assigned to a certain POIs, we create a generic POIs
            else:
                genericPoiId = "generic_"+str(genericPoiIdCounter)
                from_poi = Point_of_Interest(genericPoiId, req.attrib.get("fromEdge"))
                from_poi.pos = float(req.attrib.get("fromEdgePosition"))
                from_poi.poi_type = "genericPOI"
                from_poi.road = req.attrib.get("fromEdge")
                genericPoiId = "generic_"+str(genericPoiIdCounter + 1)
                genericPoiIdCounter += 1
                to_poi = Point_of_Interest(genericPoiId, req.attrib.get("toEdge"))
                to_poi.pos = float(req.attrib.get("toEdgePosition"))                
                to_poi.poi_type = "genericPOI"
                to_poi.road = req.attrib.get("toEdge")
                
            if from_poi and to_poi:
                dreq = DotDict()
                dreq.from_poi = from_poi
                dreq.to_poi = to_poi
                dreq.submit_time = int(req.attrib.get("submitTime"))
                checked_requests.append(dreq)

                if from_poi not in poi_arr:
                    from_poi.idx = len(poi_arr)
                    poi_arr.append(from_poi)
                if to_poi not in poi_arr:
                    to_poi.idx = len(poi_arr)
                    poi_arr.append(to_poi)
                

        self.data.poi = poi_arr + parking
        for i, poi in enumerate(self.data.poi):
            if poi.idx == None:
                poi.idx = i
            else:
                assert poi.idx == i

        self.data.parking = [
            poi for poi in self.data.poi if poi.poi_type == PARKING_POI
        ]
        self.data.distances = poi_mgr.dist_matrix(traci, poi_arr=self.data.poi)

        unsorted = []
        # iterate XML-requests a second time, now they have already valid POIs
        for req in checked_requests:
            from_idx = req.from_poi.idx
            to_idx = req.to_poi.idx

            calculated_distance = self.data.distances.dist_array[from_idx][to_idx]
            calculated_time = self.data.distances.time_array[from_idx][to_idx]
            request = Request(
                req.from_poi,
                req.to_poi,
                submit_time=req.submit_time,
                calculated_distance=calculated_distance,
                calculated_time=calculated_time,
            )
            request.from_idx = from_idx
            request.to_idx = to_idx
            request.measure = True
            unsorted.append(request)

        self.data.speed = poi_mgr.get_speed()
        self.data.requests = sorted(
            unsorted, key=lambda r: r.submit_time, reverse=False
        )
        write_pickle(self.data.project_file, self.data)
        dlog(f"Project saving {self.data.project_file} with {len(self.data.requests)} ")

    def print_requests_routes(self):
        for req in self.data.requests:
            log(f"{req.idx:3d} {req.submit_time:4d} {req.latest_finish_time:4d}")

        for i, route in enumerate(self.data.routes):
            log(f"{i:2d}: {route.reservations}")

    def set_max_delay(self, call_to_start, realistic_time=2.0, late_time=1.25):
        self.data.realistic_time = realistic_time
        self.data.late_time = late_time
        self.data.call_to_start = call_to_start

        if self.data.requests:
            for r in self.data.requests:
                r.set_max_delay(
                    call_to_start=call_to_start,
                    realistic_time=realistic_time,
                    late_time=late_time,
                )

    def get_requests(self):
        return self.data.requests

    def get_routes(self):
        return self.data.routes

    def check_route(self, route):
        full_dist = 0
        to_idx = None
        for i in route.path:
            from_idx = i
            if to_idx:
                full_dist += self.data.distances.dist_array[from_idx][to_idx]
            to_idx = from_idx

        km = full_dist / 1000
        dlog(f"{km:8.3f} km")

    def check_shared(self, routes):
        requests = self.data.requests
        # sorted_req = sorted(requests, key=lambda r: r.idx)
        req_indices = [r.idx for r in requests]

        fullfilled = []
        for route in routes:
            fullfilled += route.fullfilled
            self.check_route(route)

        duplicates = [i for i in fullfilled if fullfilled.count(i) > 1]
        if duplicates:
            elog(f"duplicates: {duplicates}")

        not_served = [i for i in req_indices if i not in fullfilled]
        if not_served:
            elog(f"not served: {not_served}")

        log(f"{len(routes)} vehicles")

    def calc_variants(self, realistic_time):
        self.data.realistic_time = realistic_time
        return sharing(
            self.data.requests, self.data.distances, self.data.speed / realistic_time
        )

    def calc_shared(self, realistic_time):
        self.init_sumo()
        self.data.realistic_time = realistic_time
        self.data.requests = check_requests(self.data.requests)
        variants = sharing(
            self.data.requests, self.data.distances, self.data.speed / realistic_time
        )
        dlog(f"variants on time_safety {realistic_time}: {len(variants)} ")

        self.data.routes = routing_with_variants(
            0, self.data.requests, variants, self.data.distances, realistic_time
        )
        write_pickle(self.data.project_file, self.data)
        return len(self.data.routes)  # num of vehicles

    def save(self):
        dir = os.path.dirname(self.data.sumo_config_file)
        filename = (
            f"P{self.data.no_of_poi}T{self.data.no_of_trips}L{self.data.delay}.pickle"
        )
        project_file = os.path.abspath(os.path.join(dir, filename))
        write_pickle(project_file, self.data)

    def cleanup(self):
        traci.close()

    def init_sumo(self):
        if self.traci_started:
            sumoStart = [
                "-S",
                "--device.taxi.dispatch-algorithm",
                "traci",
                "-c",
                self.data.sumo_config_file,
            ]
            traci.load(sumoStart)
            dlog(f"traci.load: {sumoStart}")

        else:
            atexit.register(self.cleanup)

            sumoBinary = ""
            if self.data.show_gui == "True":
                sumoBinary = checkBinary("sumo-gui")
                dlog(f"Starting SUMO in GUI - Mode...")
            else:
                sumoBinary = checkBinary("sumo")
                dlog(f"Starting SUMO without GUI...")
            sumoStart = [
                sumoBinary,
                "-S",
                "-W",
                "-Q",
                "--device.taxi.dispatch-algorithm",
                "traci",
                "-c",
                self.data.sumo_config_file,
            ]
            traci.start(sumoStart)
            self.traci_started = True
            dlog(f"traci.start: {sumoStart}")

    def run_requests(self, strategy: str = "simple"):
        self.init_sumo()
        num_of_vehicles = 0

        if Request.manager:
            Request.manager.set_requests(self.data.requests)
            Request.manager.sumo_public["strategy"] = strategy

        if strategy == "simple":
            simple_strategy(self.data)
            num_of_vehicles = self.data.no_of_vehicles

        if strategy == "shared":
            shared_strategy(self.data)
            num_of_vehicles = len(self.data.routes)

        if strategy == "look_ahead":
            look_ahead_strategy(self.data)
            num_of_vehicles = self.data.no_of_vehicles

        if Request.manager:
            res = Request.manager.get_result()
            res["num_of_vehicles"] = num_of_vehicles
            res["strategy"] = strategy
            if strategy == "look_ahead":
                res["look_ahead_time"] = self.data.look_ahead_time

            res["call_to_start"] = self.data.call_to_start

            return res
