# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: November 2020
# License: MIT License
# =============================================================================
# This Script uses OsmApi to converts Points of Interest (POIs) from
# Open Street Map (OSM) GeoCoordinates to Edge IDs and Edge Positions which can
# be used by SUMO as Start- or Targetpoints.
# =============================================================================

import os
import sys
from sumohelper.CoordModification import norm_distribution_algorithm, equidistant_circles_algorithm

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Bitte Umgebungsvariable 'SUMO_HOME' definieren!")

from sumolib import checkBinary as checkBinary
import traci as traci
from traci.exceptions import TraCIException, FatalTraCIError


class EdgeFinder:
    def __init__(self, sumocfg: str):
        try:
            # SUMO has to be started otherwise we cant use the method "traci.simulation.convertRoad()"
            traci.start(
                [
                    checkBinary("sumo"),
                    "-c",
                    sumocfg,
                    "--tripinfo-output",
                    "tripinfo.xml",
                ]
            )
        except:
            raise ("Could not start TraCI/Sumo")

    def findBestFittingEdge(self, lat: float, long: float, edges_list: [], allow_correction: bool,
                            corr_algorithm: str = "eqdistcircles",
                            max_matching_distance_meters: int = 500):
        edgeID, lanePosition, laneIndex = None, None, None
        try:
            edgeID, lanePosition, laneIndex = self.findNearestEdge(lat=lat, long=long)
        except RuntimeError as e:
            pass
        if edgeID in edges_list:
            return edgeID, lanePosition, laneIndex
        if not allow_correction:
            raise RuntimeError("ERROR: nearest edge not found in 'edges_list'. You might use 'allow_correction'-flag")
        iteration = 0
        while edgeID not in edges_list:
            iteration += 2
            if corr_algorithm == "normdist":
                new_lat, new_long, dist_meters = norm_distribution_algorithm(lat=lat, long=long, iteration=iteration,
                                                                             max_matching_distance_meters=max_matching_distance_meters)
            elif corr_algorithm == "eqdistcircles":
                new_lat, new_long, dist_meters = equidistant_circles_algorithm(lat=lat, long=long, iteration=iteration,
                                                                               max_matching_distance_meters=max_matching_distance_meters)
            else:
                raise RuntimeError(f"ERROR: Unknown 'corr_algorithm': '{corr_algorithm}'")
            print(f"WARNING: Added random norm value on lat and long to find allowed match with edgeId: {edgeID}"
                  f"distance({dist_meters}m, lat-diff: {new_lat - lat}, long-diff: {new_long - long})")
            try:
                edgeID, lanePosition, laneIndex = self.findNearestEdge(lat=new_lat, long=new_long)
            except RuntimeError as e:
                continue
        return edgeID, lanePosition, laneIndex

    def findNearestEdge(self, lat: float, long: float):
        try:
            (
                edgeID,
                lanePosition,
                laneIndex,
            ) = traci.simulation.convertRoad(long, lat, True)
        except TraCIException as e:
            raise RuntimeError(f"Could not find nearest edge for coord({lat},{long})")
        return edgeID, lanePosition, laneIndex
