#!/usr/bin/env python3

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

import osmapi as osm
import lxml.etree as ET
import os
import sys
from PoiModules.EdgeFilter import EdgeFilter

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Bitte Umgebungsvariable 'SUMO_HOME' definieren!")

from sumolib import checkBinary as checkBinary
import traci as traci


class Poi2EdgeConverter:
    def __init__(self):
        self.edgeFilter = EdgeFilter()

           
    def convertPois2Edges(self, filter, workingDir):
        print("The current Working Directory is: ", workingDir)

        print("Converting the following POIs to Edge Positions: ", filter)
        print("Read reference Edge...")

        reference_edge = ""

        # reading the reference Edge from referenceEdge.xml to check if our current POI has a valid route to the reference Edge, which should be in the center of the map
        # e.g. for the Mannheim Model we use the reference_edge "4087264" (Friedrich-Ebert-Straße) to check if routes to and from this edge can be found

        try:
            refEdgeTree = ET.parse(workingDir+"/referenceEdge.xml")
            refEdgeRoot = refEdgeTree.getroot()
            
            reference_edge = refEdgeRoot.get("id")
            print("The Edge Id "+ reference_edge + " was successfully set as reference Edge")

        except:
            print("----------------------------------------------------------------------------------")
            print("Error: There is no valid referenceEdge.xml File in your current SUMO Model Directory !!!")
            print("A reference needs to be specified to find valid routing paths ")
            print("Please create therefore a File with the name referenceEdge.xml in your SUMO Model Directory") 
            print("Specify there the reference edge Id (e.g. an Edge Id from the center of your Model)")
            print("The File Content looks like the following example:")
            print("----------------------------------------------------------------------------------")
            print("<?xml version='1.0' encoding='UTF-8'?>")
            print("<referenceEdge id = \"45085545\"/>")            
            print("----------------------------------------------------------------------------------")
        
        # now we use the osm.OsmApi() to extract Information from the POIs:
        
        try:
            api = osm.OsmApi()

            # SUMO has to be started otherwise we cant use the method "traci.simulation.convertRoad()"
            traci.start(
                [
                    checkBinary("sumo"),
                    "-c",
                    workingDir+"/osm.sumocfg",
                    "--tripinfo-output",
                    "tripinfo.xml",
                ]
            )
            polyTree = ET.parse("osm.poly.xml")
            polyRoot = polyTree.getroot()

            edgePositions = ET.Element("edgelist")

            poisEdges = ET.Element("poi_collection")

            # all <poly> - Tags (which stands for "polygon") have an attribute "shape" that defines the border of the structure
            # if no filter is given the filter is read from POI_View_Settings.xml
            if len(filter) == 0:
                settingsTree = ET.parse(workingDir+"/POI_View_Settings.xml")
                settingsRoot = settingsTree.getroot()

                # read poly- Settings
                for setting in settingsRoot.findall("poly"):
                    filter.append(setting.attrib.get("type"))
                # read poi- Settings
                for setting in settingsRoot.findall("poi"):
                    filter.append(setting.attrib.get("type"))

            print("The current Working Directory is: ", workingDir)

            print("Converting the following POIs to Edge Positions: ", filter)
            # reading poly - Tags from osm.poly.xml
            for poly in polyRoot.findall("poly"):
                polyType = poly.attrib.get("type")

                if polyType in filter:
                    try:
                        id = poly.attrib.get("id")
                        # exctract additional information for the current <poly> entity via the OsmApi
                        way = api.WayGet(id)

                        # now we can extract the corner- points (nodes) for the current "parking" entity
                        nodes = way["nd"]

                        # as we get the corner points of the POI - polygon we face the problem, that some points
                        # could refer to one edge (lane) and some to another edge (lane).
                        # the simplest was is to count which edge (lane) is picked most by the API and edge (lane) we will assign
                        # we use a dictionary with follwing structure {edgeID : [edgeCounter, minPos, maxPos]}
                        # to assign the edge with the highest count and to calculate the intermediate edgeposition
                        lanes = {}

                        for node in nodes:
                            # for each node we have to use the OsmApi again to get the node - position
                            nodesInfo = api.NodeGet(node)
                            lon = nodesInfo["lon"]
                            lat = nodesInfo["lat"]
                            (
                                edgeID,
                                lanePosition,
                                laneIndex,
                            ) = traci.simulation.convertRoad(
                                float(lon), float(lat), True
                            )

                            laneID = edgeID + "_" + str(laneIndex)

                            if laneID not in lanes:
                                lanes[laneID] = [1, lanePosition, lanePosition]
                            else:
                                lanes[laneID][0] += 1
                                if lanePosition < lanes[laneID][1]:
                                    lanes[laneID][1] = lanePosition
                                if lanePosition > lanes[laneID][2]:
                                    lanes[laneID][2] = lanePosition

                        laneToAssign = ""
                        maxCounter = 0

                        # here we assign the lane with the highest count for the current POI
                        for l in lanes:
                            if lanes[l][0] > maxCounter:
                                maxcounter = lanes[l][0]
                                laneToAssign = l

                        startPos = lanes[laneToAssign][1]
                        endPos = lanes[laneToAssign][2]

                        middlePos = format((startPos + endPos) / 2, ".2f")
                        print(way["tag"])

                        ET.SubElement(edgePositions, 'poly', id=id, type = polyType, lane=laneToAssign, lane_position = str(middlePos), details = str(way['tag']))
                        ET.SubElement(poisEdges, 'poi', id=id, type = polyType, edge_id= poi_Edge, lane_position = str(middlePos), lane_index = l_index)
                        
                        # now we use the reference Edge which was read before from referenceEdge.xml to check if our current POI has a valid route to the reference Edge (which should be in the center of the map)
                        poi_Edge = laneToAssign[:laneToAssign.index('_')]
                        l_index = laneToAssign[laneToAssign.index('_'):]
                        
                        print("Searching for Route from ",poi_Edge, " to ",reference_edge )
                        
                        try:
                            toRoute = traci.simulation.findRoute(poi_Edge, reference_edge, "taxi")
                            fromRoute = traci.simulation.findRoute(reference_edge, poi_Edge, "taxi")
                            print("toRoutes: ",len(toRoute.edges))
                            print("fromRoutes: ",len(fromRoute.edges))    
                            if toRoute and len(toRoute.edges) > 0 and fromRoute and len(fromRoute.edges) >0:
                                ET.SubElement(edgePositions, 'poly', id=id, type = polyType, lane=laneToAssign, lane_position = str(middlePos), details = str(way['tag']))
                                ET.SubElement(poisEdges, 'poi', id=id, type = polyType, edge_id= poi_Edge, lane_position = str(middlePos), lane_index = l_index)
                        except:
                            print("Skipped Type ",polyType, "because no valid route could be found")
                    except:
                        print(
                            "Skipped Type ",
                            polyType,
                            "because no valid edge could be found",
                        )
            # reading poi - Tags from osm.poly.xml
            for poi in polyRoot.findall("poi"):
                poiType = poi.attrib.get("type")

                if poiType in filter:
                    try:
                        id = poi.attrib.get("id")

                        # get further information about the node from the OSM API
                        nodeInfo = api.NodeGet(id)
                        lon = nodeInfo["lon"]
                        lat = nodeInfo["lat"]

                        # find the edgeId and the LanePosition for a given POI position
                        # the flag "True" indicates, that we are using GeoPosition instead of x,y Position
                        edgeID, lanePosition, laneIndex = traci.simulation.convertRoad(
                            float(lon), float(lat), True
                        )

                        laneID = edgeID + "_" + str(laneIndex)

                        print(nodeInfo)
                        nodeDetails = " "

                        if "tag" in nodeInfo:
                            nodeDetails = str(nodeInfo["tag"])
                        print(id, poiType, laneID, str(lanePosition))
                        ET.SubElement(edgePositions, 'poi', id=id, type = poiType, lane=laneID, lane_position = str(format(lanePosition, '.2f')), details = nodeDetails)
                        ET.SubElement(poisEdges, 'poi', id=id, type = poiType, edge_id= str(edgeID), lane_position = str(lanePosition), lane_index = str(laneIndex))
                        # now we use the reference Edge which was read before from referenceEdge.xml to check if our current POI has a valid route to the reference Edge (which should be in the center of the map)

                        print("-----------------------------------------------------------")
                        print("Searching for Route from ",edgeID, " to ",reference_edge )
                        try:
                            toRoute = traci.simulation.findRoute(edgeID, reference_edge, "taxi")
                            print("toRoutes: ",len(toRoute.edges))
                            fromRoute = traci.simulation.findRoute(reference_edge, edgeID, "taxi")
                            print("fromRoutes: ",len(fromRoute.edges))    
                            if toRoute and len(toRoute.edges) > 0 and fromRoute and len(fromRoute.edges) >0:
                                ET.SubElement(edgePositions, 'poi', id=id, type = poiType, lane=laneID, lane_position = str(format(lanePosition, '.2f')), details = nodeDetails)
                                ET.SubElement(poisEdges, 'poi', id=id, type = poiType, edge_id= str(edgeID), lane_position = str(lanePosition), lane_index = str(laneIndex))
                        except:
                            print("Skipped Type ",poiType, "because no valid route could be found")

                    except:
                        print(
                            "Skipped Type ",
                            poiType,
                            "because no valid edge could be found AUSSEN",
                        )

            edgePositionsTree = ET.ElementTree(edgePositions)
            poisEdgesTree = ET.ElementTree(poisEdges)
            # formatting and writing the xml file
            edgePositionsTree.write(
                workingDir+"/EdgePositions.xml",
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )

            poisEdgesTree.write(
                workingDir+"/POIsEdges.xml",
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )
            try:
                traci.close()
                sys.stdout.flush()
            except:
                print("closing traci caused Problems")

            print("READY!")

        except:
            print(
                "An Error has occurred: please check if the input file is a valid xml file"
            )

    def getPoiIfValid(self, poi):
        poiEdge = poi["edge"]

        # here we lookup in the validEdgeDict whether our picked POI has as a valid edge for waiting persons
        if poiEdge in self.edgeFilter.validEdgeDict.keys():
            return poi

        # if the current POI edge is not a valid edge, we try with the opposite (inverse) edge
        inversePoiEdge = self.edgeFilter.getInverseEdge(poiEdge)
        if inversePoiEdge is not None:
            print(
                "NOTE: The Edge",
                poiEdge,
                "at POI",
                poi["type"],
                "is not valid for waiting persons, but the opposite Edge",
                inversePoiEdge,
                "is used instead",
            )
            poi["edge"] = inversePoiEdge
            # due to the fact that we are now using the opposite edge we have to calculate the mirrowed edge position
            poi["position"] = str(
                "{:.2f}".format(
                    abs(
                        float(self.edgeFilter.validEdgeDict[inversePoiEdge])
                        - float(poi["position"])
                    )
                )
            )
            return poi
        else:
            print(
                "NOTE: The POI ",
                poi["type"],
                " at Edge ",
                poiEdge,
                " was dropped because this Edge is not valid for waiting persons!",
            )
            return None

    def readEdgeList(self,workingDir):
        poiList = []
        try:
            edgeTree = ET.parse(workingDir+"/EdgePositions.xml")
            edgeRoot = edgeTree.getroot()

            for poi in edgeRoot.findall("poi"):

                element = {
                    "id": poi.attrib.get("id"),
                    "type": poi.attrib.get("type"),
                    # to get the edgeId we remove the lane number at the end of the laneId including the last "_"
                    "edge": poi.attrib.get("lane")[: poi.attrib.get("lane").rfind("_")],
                    "position": poi.attrib.get("lane_position"),
                    "details": poi.attrib.get("details"),
                }
                validPoi = self.getPoiIfValid(element)
                if validPoi:
                    poiList.append(validPoi)

            for poi in edgeRoot.findall("poly"):
                element = {
                    "id": poi.attrib.get("id"),
                    "type": poi.attrib.get("type"),
                    # to get the edgeId we remove the lane number at the end of the laneId including the last "_"
                    "edge": poi.attrib.get("lane")[: poi.attrib.get("lane").rfind("_")],
                    "position": poi.attrib.get("lane_position"),
                    "details": poi.attrib.get("details"),
                }
                validPoi = self.getPoiIfValid(element)
                if validPoi:
                    poiList.append(validPoi)
        except:
            print(
                "An Error has occurred: please check if the input file is a valid xml file"
            )
            return None
        return poiList
