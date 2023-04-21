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

import pandas as pd

from Net.point_of_interest import Point_of_Interest
from Moving.request import Request
from KI4RoboRoutingTools.Request_Creation.sumohelper.EdgeCoordsAccess import EdgeCoord
from KI4RoboRoutingTools.Request_Creation.sumohelper.SectorCoordsAccess import SectorCoord
import os
import lxml.etree as ET


class ProjectConfigData:
    def __init__(self, sumo_config_file: str, project_file: str, **kwargs):
        self.show_gui = kwargs.get("show_gui", True)
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
        self.create_dist_matrix = kwargs.get("create_dist_matrix", False)
        self.skip_find_route_to_clean_edge = kwargs.get("skip_find_route_to_clean_edge", False)
        self.edge_coords_file = kwargs.get("edge_coords_file", None)
        self.sector_coords_file = kwargs.get("sector_coords_file", None)
        self.sup_learn_training_data_file = kwargs.get("sup_learn_training_data_file", None)

        self.poi: List[Point_of_Interest] = None
        self.parking: List[Point_of_Interest] = None
        self.distances = None
        self.speed = None
        self.requests: List[Request] = None
        self.routes = None
        self.edge_coords: List[EdgeCoord] = None
        self.sector_coords: List[SectorCoord] = None
        self.sup_learn_training_data: pd.DataFrame = None


def project_config_from_options(options) -> ProjectConfigData:
    if options.sumo_config_file and options.project_file:
        c = ProjectConfigData(options.sumo_config_file, options.project_file)
    for att, value in options.__dict__.items():
        if att in c.__dict__:
            c.__dict__[att] = value

    # The refenece Edge is read from the File referenceEdge.xml
    try:
        referenceEdgeFilePath = os.path.dirname(c.sumo_config_file)+"/referenceEdge.xml"
        refEdgeTree = ET.parse(referenceEdgeFilePath)
        refEdgeRoot = refEdgeTree.getroot()
        reference_edge = refEdgeRoot.get("id")
        c.clean_edge = reference_edge
        print("--------------------------------------------------------------------------------------------------")
        print("The Edge Id "+ reference_edge + " was successfully read from ",referenceEdgeFilePath+" and is set as reference Edge for routing checks")
        print("--------------------------------------------------------------------------------------------------")
    except:
        print("----------------------------------------------------------------------------------")
        print("There is no valid referenceEdge.xml File in your current SUMO Model Directory")
        print("Therefore the reference edge 45085545 (Citycenter of Mannheim) is used")
    return c
