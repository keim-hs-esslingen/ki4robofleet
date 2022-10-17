#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides the SumoReader- Class to
# read the XML Config, extract sub files
#    Extract Parking-Areas and Points-of-Interest
# =============================================================================

import os
import random
from typing import List


import json
from Tools.logger import log, elog, ylog

from termcolor import colored
import xml.etree.ElementTree as ET
from pathlib import Path

from Tools.dotdict import DotDict
from Net.point_of_interest import Point_of_Interest, PARKING_POI
from Net.poi_manager import POI_Manager


class Edge:
    def __init__(self, eid, typ, streetname):
        self.eid = eid
        self.type = typ
        self.lanes = []
        self.road = None
        self.name = streetname
        self.walk_lane = None
        self.vehicle_lane = None
        self.from_to = []

    def dd(self):
        d = DotDict()
        d.edge = self.eid
        d.type = self.type
        d.name = self.name
        return d


class SumoReader:
    def __init__(self, pm: POI_Manager):
        self.street_dict = {}
        self.lane_dict = {}
        self.poi_mgr = pm
        self.poiColorDict = {}
        self.edge_dict = {}

    def read_config(self, filename, dbg=False):
        print(f"SUMO config {filename}")
        parent = os.path.dirname(filename)
        netTree = ET.parse(filename)
        netRoot = netTree.getroot()
        # Assumes that there is only ONE netfile in the config
        netfile = netRoot.findall("*/net-file")[0].attrib.get("value")
        netfilepath = Path(parent).joinpath(netfile)
        self.read_net(netfilepath, dbg)

        addfiles = netRoot.findall("*/additional-files")[0].attrib.get("value")

        add_arr = addfiles.split(",")
        for filename in add_arr:
            filepath = Path(parent).joinpath(filename.strip())
            self.read_additional(filepath)

        # read POI colors from POI_View_Settings.xml
        addViewSettings = Path(parent).joinpath("POI_View_Settings.xml")
        self.read_poi_colors(addViewSettings, dbg)

        addilepath = Path(parent).joinpath("POIsEdges.xml")
        self.read_poi_edges(addilepath, dbg)

    def read_net(self, filename, dbg=False):
        print(f"SUMO net {filename}")
        netTree = ET.parse(filename)
        netRoot = netTree.getroot()

        # test_edges = ["178193953"]
        test_edges = []

        from_to = {}
        connections = netRoot.findall("connection")
        for connect in connections:
            from_edge = connect.attrib.get("from")
            to_edge = connect.attrib.get("to")
            if from_edge in from_to:
                from_to[from_edge].append(to_edge)
            else:
                from_to[from_edge] = [to_edge]

        edges = netRoot.findall("edge")
        for edge in edges:
            edge_id = edge.attrib.get("id")
            edge_type = edge.attrib.get("type")
            street = edge.attrib.get("name")
            if ":" in edge_id:
                continue
            if edge_id in test_edges:
                print("test ", edge_id)
            #
            edge_obj = Edge(edge_id, edge_type, street)
            if street not in self.street_dict:
                self.street_dict[street] = [edge_id]
            else:
                self.street_dict[street].append(edge_id)

            lanes = edge.findall("lane")
            for lane in lanes:
                lane_id = lane.attrib.get("id")
                self.lane_dict[lane_id] = edge_id
                self.poi_mgr.add_lane_to_edge(edge_id, lane_id)
                allows = lane.attrib.get("allow")
                if allows:
                    if "pedestrian" in allows:
                        edge_obj.walk_lane = lane_id
                    if "passenger" in allows:
                        edge_obj.vehicle_lane = lane_id
                else:
                    edge_obj.vehicle_lane = lane_id
            if edge_obj.vehicle_lane:
                edge_obj.road = edge_id

            if edge_id in from_to:
                edge_obj.from_to = from_to[edge_id]
            self.edge_dict[edge_id] = edge_obj

    def has_road(self, eid):
        if eid in self.edge_dict:
            edge_obj: Edge = self.edge_dict[eid]
            if edge_obj.vehicle_lane:
                return eid
            return edge_obj.road
        return None

    def read_additional(self, filename, dbg=False):
        print(f"SUMO add {filename}")
        netTree = ET.parse(filename)
        netRoot = netTree.getroot()
        parkingareas = netRoot.findall("parkingArea")
        no_road_counter = 0
        road_counter = 0
        for parking in parkingareas:
            park_id = parking.attrib.get("id")
            lane_id = parking.attrib.get("lane")
            if lane_id in self.lane_dict:
                edge_id = self.lane_dict[lane_id]
                poi_obj = Point_of_Interest(park_id, edge_id)
                poi_obj.poi_type = PARKING_POI
                poi_obj.park_id = park_id
                poi_obj.road = self.has_road(edge_id)
                if poi_obj.road:
                    edge: Edge = self.edge_dict[edge_id]
                    poi_obj.walk_lane = edge.walk_lane
                    poi_obj.road_lane = edge.vehicle_lane
                    self.poi_mgr.add(poi_obj)
                    road_counter += 1
                else:
                    no_road_counter += 1
        print(f"road parking {road_counter} / {no_road_counter}")

        """
        Example for Point of Interest Color in the XML File:
        <poi type="amenity.school" color="255,150,0" layer="1.00"/>
        """

    def read_poi_colors(self, filename, dbg=False):
        print(f"SUMO add {filename}")
        try:
            settingsTree = ET.parse(filename)
            settingsRoot = settingsTree.getroot()
            poiSettings = settingsRoot.findall("poi")
            polySettings = settingsRoot.findall("poly")

            for setting in poiSettings + polySettings:
                self.poiColorDict[setting.attrib.get("type")] = setting.attrib.get(
                    "color"
                ).split(",")
                ylog(
                    f"Setting Color for {setting.attrib.get('type')} : {setting.attrib.get('color')}"
                )

        except FileNotFoundError:
            print(
                "The File POI_View_Settings.xml was not found -> no Color Information for Points of Interst could be read!"
            )

        """
        Example for Point of Interest Edge Information in POIsEdges.xml:
        <poi id="1001227270" type="amenity.fast_food" name="Asia Imbiss Panda" lon="8.47542" lat="49.48802" edge_id="268931682#0" lane_position="1.040" lane_index="0"/>
        """

    def read_poi_edges(self, filename, dbg=False):
        print(f"SUMO add {filename}")
        netTree = ET.parse(filename)
        netRoot = netTree.getroot()
        point_of_interest = netRoot.findall("poi") + netRoot.findall("poly")
        no_road_counter = 0
        road_counter = 0
        for poi in point_of_interest:
            poi_id = poi.attrib.get("id")
            edge_id = poi.attrib.get("edge_id")
            poi_type = poi.attrib.get("type")
            poi_obj = Point_of_Interest(poi_id, edge_id)
            poi_obj.poi_type = poi_type

            # assign POI color if value was specified in POI_View_Settings.xml
            if poi_type in self.poiColorDict.keys():
                poi_obj.color = self.poiColorDict[poi_type]

            poi_obj.pos = float(poi.attrib.get("lane_position"))
            if poi_obj.pos < 0:
                elog(f"reset pos at {edge_id} {poi_type} {poi_obj.pos}")
                poi_obj.pos = 0
            poi_obj.road = self.has_road(edge_id)
            if poi_obj.road:
                edge: Edge = self.edge_dict[edge_id]
                poi_obj.walk_lane = edge.walk_lane
                poi_obj.road_lane = edge.vehicle_lane
                self.poi_mgr.add(poi_obj)  # add to poi manager
                road_counter += 1
            else:
                no_road_counter += 1
        print(f"road poi {road_counter} / {no_road_counter}")

    def clean_roads(self, traci, start_edge):
        filtered = [v for k, v in self.edge_dict.items() if v.vehicle_lane]

        roads = DotDict()

        roads.valid = []
        valid_edges = []

        # fix for #9
        for i, edge in enumerate(filtered):
            valid_edges.append(edge.eid)
            roads.valid.append(edge.dd())
            continue
            stage_to = traci.simulation.findRoute(start_edge, edge.eid)
            stage_from = traci.simulation.findRoute(edge.eid, start_edge)
            if (
                stage_to
                and len(stage_to.edges) > 0
                and stage_from
                and len(stage_from.edges) > 0
            ):
                valid_edges.append(edge.eid)
                roads.valid.append(edge.dd())

        self.poi_mgr.clean(valid_edges)
        roads.poi = [poi.dd() for poi in self.poi_mgr.poi_arr]
        parking = [poi for poi in self.poi_mgr.poi_arr if poi.poi_type == PARKING_POI]

        log(f"{len(roads.valid)} valid road edges; from {start_edge}")
        log(f"{len(parking)} valid parking")
        log(f"{len(roads.poi)} valid POI")

        to_dump = [str(poi) for poi in self.poi_mgr.poi_arr]

        f = open("cleaned_POI.txt", "w")
        f.write("\n".join(to_dump))
        f.close()
