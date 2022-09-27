#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: December 2020
# License: MIT License
# =============================================================================
# This Script converts Parking Areas from OpenStreet POIs to Parking Areas
# which can be utilized by SUMO
# =============================================================================

import osmapi as osm

import lxml.etree as ET

import os
import sys

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Bitte Umgebungsvariable 'SUMO_HOME' definieren!")

from sumolib import checkBinary
import traci


class ParkingAreaConverter:
    def convertParkingAreas(self, osmPolyFile, defaultCapacity=1, parkingLotLength=5.0):
        # if the capacity of a parking Area can't be retrieved from the osmapi
        # we define here a defaultCapacity which will be assigned in this case
        self.defaultCapacity = defaultCapacity

        # here we define how long a parking lot will be drawn in the map
        self.parkingLotLength = parkingLotLength
        try:
            api = osm.OsmApi()

            # SUMO has to be started otherwise we cant use the method "traci.simulation.convertRoad()"
            traci.start(
                [
                    checkBinary("sumo"),
                    "-c",
                    os.path.dirname(osmPolyFile)+"/osm.sumocfg",
                    "--tripinfo-output",
                    "tripinfo.xml",
                ]
            )
            polyTree = ET.parse(osmPolyFile)
            polyRoot = polyTree.getroot()

            xml_output = ET.Element("additional")

            parkingAreaDict = {}

            # since the "parking" entities are not located in the <poi> tags b
            # but in the <poly> tags we iterate over all these tags
            for poly in polyRoot.findall("poly"):
                polyType = poly.attrib.get("type")
                # filter all "parking" entities
                if ("parking" in polyType) and ("bicycle_parking" not in polyType):
                    id = poly.attrib.get("id")
                    # exctract additional information for the current "parking" entity via the OsmApi
                    way = api.WayGet(id)

                    print("parking entity with ID ", id, " is being converted...")
                    # now we can extract the corner- points (nodes) for the current "parking" entity
                    nodes = way["nd"]

                    # we use a dictionary with follwing structure {edgeID : [edgeCounter, minPos, maxPos]}
                    # to assign the edge with the highest count and to calculate the intermediate edgeposition
                    lanes = {}

                    for node in nodes:
                        # for each node we have to use the OsmApi again to get the node - position
                        nodesInfo = api.NodeGet(node)
                        lon = nodesInfo["lon"]
                        lat = nodesInfo["lat"]

                        # here the current node is assigned to an edge (lane)
                        edgeID, lanePosition, laneIndex = traci.simulation.convertRoad(
                            float(lon), float(lat), True
                        )

                        laneID = edgeID + "_" + str(laneIndex)

                        if laneID not in lanes:
                            lanes[laneID] = [1, lanePosition]
                        else:
                            lanes[laneID][0] += 1
                            if lanePosition < lanes[laneID][1]:
                                lanes[laneID][1] = lanePosition

                    # now we have to decide which lane should be assigned to the current parking Area
                    laneToAssign = ""
                    maxCounter = 0

                    for l in lanes:
                        # here we check which lane occurs most often in the list and this one will be assigned finally
                        # we also remove crossings because parkingAreas ar crossings are not common and appear ugly in the map
                        if (lanes[l][0] > maxCounter) and (":" not in l):
                            maxCounter = lanes[l][0]
                            laneToAssign = l

                    # if no lane could be assigned we ignore and skip the current parkingArea
                    if len(laneToAssign) == 0:
                        continue

                    startPos = format(lanes[laneToAssign][1], ".2f")

                    # if no information about the capacity is given the specified defaultCapacity will be assigned
                    capacity = self.defaultCapacity

                    # else try to extract the capacity from the tag
                    if "tag" in way:
                        if "capacity" in way["tag"]:
                            capacity = way["tag"]["capacity"]

                    parkingArea = {
                        "capacity": capacity,
                        "lane": laneToAssign,
                        "startPos": startPos,
                    }

                    parkingAreaDict[id] = parkingArea

            # now we iterate over parkingAreaDict and we remove multiple occurance of parking Areas in one lane
            laneCheckDict = {}
            uniqueLaneParkingAreaDict = {}

            for parkingAreaId in parkingAreaDict.keys():
                currentLane = parkingAreaDict[parkingAreaId]["lane"]
                if currentLane in laneCheckDict:
                    # neglect the current parkingArea and add the capacity to the existing one
                    uniqueLaneParkingAreaDict[laneCheckDict[currentLane]][
                        "capacity"
                    ] = str(
                        int(parkingAreaDict[laneCheckDict[currentLane]]["capacity"])
                        + int(parkingAreaDict[parkingAreaId]["capacity"])
                    )
                else:
                    uniqueLaneParkingAreaDict[parkingAreaId] = parkingAreaDict[
                        parkingAreaId
                    ]
                    laneCheckDict[currentLane] = parkingAreaId

            # now we write the xml Entries from the clean uniqueLaneParkingAreaDict
            for parkingAreaId in uniqueLaneParkingAreaDict.keys():
                uniqueLaneParkingArea = uniqueLaneParkingAreaDict[parkingAreaId]
                capacity = uniqueLaneParkingArea["capacity"]
                startPos = uniqueLaneParkingArea["startPos"]

                # this step helps to avoid too narrow parking Lots
                if int(capacity) > 5:
                    startPos = "0"

                # since it is very hard to determine the lane length we just calculate the endPos of the ParkingArea
                # if the calculated value is higher than the whole lane length it causes no problems and is cut by SUMO
                # to the lane length
                endPos = float(startPos) + int(capacity) * self.parkingLotLength
                ET.SubElement(
                    xml_output,
                    "parkingArea",
                    id=parkingAreaId,
                    lane=uniqueLaneParkingArea["lane"],
                    friendlyPos="true",
                    roadsideCapacity=str(capacity),
                    startPos=startPos,
                    endPos=str(endPos),
                )

            tree = ET.ElementTree(xml_output)

            # formatting and writing the xml file
            tree.write(
                os.path.dirname(osmPolyFile)+"/parkingAreas.xml",
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )
            traci.close()
            sys.stdout.flush()
            print(
                "READY: 'parkingAreas.xml' was created, please include this file in osm.sumocfg as additional file"
            )

        except:
            print(
                "An Error has occurred: please check if the input file is a valid xml file"
            )
