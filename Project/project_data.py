#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script provides the ProjectConfigData- Class to store
# Parameters and Settings for the Simulation
# =============================================================================

from typing import List

from Net.point_of_interest import Point_of_Interest
from Moving.request import Request
from Tools.logger import log


class ProjectConfigData:
    def __init__(self, sumo_config_file: str, project_file: str, **kwargs):
        self.no_of_poi = kwargs.get("no_of_poi", 10)
        self.no_of_trips = kwargs.get("no_of_trips", 10)
        self.no_of_vehicles = kwargs.get("no_of_vehicles", 10)
        self.time_safety_factor = kwargs.get("time_safety_factor", 1.0)
        self.epoch_timeout = kwargs.get("epoch_timeout", 3600)
        self.look_ahead_time = kwargs.get("look_ahead_time", 100)
        self.requests_file = kwargs.get("requests_file", None)
        self.delay = kwargs.get("delay", 2.0)
        self.clean_edge = kwargs.get("clean_edge", "45085545")
        self.sumo_config_file = sumo_config_file
        self.project_file = project_file

        self.poi: List[Point_of_Interest] = None
        self.parking: List[Point_of_Interest] = None
        self.distances = None
        self.speed = None
        self.requests: List[Request] = None
        self.routes = None


def project_config_from_options(options) -> ProjectConfigData:
    if options.sumo_config_file and options.project_file:
        c = ProjectConfigData(options.sumo_config_file, options.project_file)
    for att, value in options.__dict__.items():
        if att in c.__dict__:
            c.__dict__[att] = value

    return c
