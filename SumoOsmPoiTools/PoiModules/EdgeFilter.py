#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script filters Edges which are not allowed for cars and with the
# Method getInverseEdge() the opposite Edge is tested as alternative if the
# original Edge is not valid
# =============================================================================


import lxml.etree as ET


class EdgeFilter:

    # dictionary: keys: valid EdgeIds values: EdgeLength
    validEdgeDict = {}

    def __init__(self, workingDir):
        try:
            netTree = ET.parse(workingDir+"/osm.net.xml")
            netRoot = netTree.getroot()

            edges = netRoot.findall("edge")

            for edge in edges:
                eid = edge.attrib.get("id")
                # edgeIds with ":" cause problems because they are intersections or are not reachable by cars
                if ":" in eid:
                    continue

                isValidEdge = False
                maxLength = 0

                lanes = edge.findall("lane")
                for lane in lanes:
                    length = float(lane.attrib.get("length"))
                    if length:
                        if maxLength < length:
                            maxLength = length
                    # this section is a bit confusing
                    # lanes usually have the attribute 'allow' or 'disallow'
                    # if the attribute 'allow' is defined it is a special lane (e.g. a bicycle lane)
                    # if the attribute 'disallow' is defined it is a common lane (e.g. for passenger cars)
                    # to position a waiting person we need an edge which contains at least one common lane
                    # otherwise errors will occur
                    disallow = lane.attrib.get("disallow")
                    if disallow:
                        isValidEdge = True

                if isValidEdge:
                    self.validEdgeDict[eid] = maxLength

        except:
            print(
                "An Error has occurred: please check if a valid 'osm.net.xml' file is in the current directory"
            )

    def getInverseEdge(self, edgeId):
        if edgeId[0] == "-":
            inverseEdgeId = edgeId[1:]
        else:
            inverseEdgeId = "-" + edgeId
        if inverseEdgeId in self.validEdgeDict.keys():
            return inverseEdgeId
        else:
            return None
