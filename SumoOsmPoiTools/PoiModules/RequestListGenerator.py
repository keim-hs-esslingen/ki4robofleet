#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: January 2021
# License: MIT License
# =============================================================================
# This script generates the Request List which defines the customer Request
# for the autonomous driving vehicles for certain Times at certain POIs
# =============================================================================

import lxml.etree as ET
import random
import numpy as np
from PoiModules.Poi2EdgeConverter import Poi2EdgeConverter
from PoiModules.PoiTypes import PoiTypeList
import os


class Scenario:
    def __init__(
        self,
        fromPoiGroup,
        fromPoiAnySubGroup,
        fromPoiSubGroup,
        toPoiGroup,
        toPoiAnySubGroup,
        toPoiSubGroup,
        numberOfRequests,
        roundTrip,
        stayTime,
        normalDistributed,
        standardDeviation,
    ):
        self.fromPoiGroup = fromPoiGroup
        self.fromPoiAnySubGroup = fromPoiAnySubGroup
        self.fromPoiSubGroup = fromPoiSubGroup
        self.toPoiGroup = toPoiGroup
        self.toPoiAnySubGroup = toPoiAnySubGroup
        self.toPoiSubGroup = toPoiSubGroup
        self.numberOfRequests = numberOfRequests
        self.roundTrip = roundTrip
        self.stayTime = stayTime
        self.normalDistributed = normalDistributed
        self.standardDeviation = standardDeviation


class Request:
    def __init__(
        self,
        id,
        submitTime,
        fromPOI,
        fromEdge,
        fromEdgePosition,
        fromDetails,
        toPOI,
        toEdge,
        toEdgePosition,
        toDetails,
        relatedId,
    ):
        self.id = id
        self.submitTime = submitTime
        self.fromPOI = fromPOI
        self.fromEdge = fromEdge
        self.fromEdgePosition = fromEdgePosition
        self.fromDetails = fromDetails
        self.toPOI = toPOI
        self.toEdge = toEdge
        self.toEdgePosition = toEdgePosition
        self.toDetails = toDetails
        self.relatedId = relatedId


class RequestListGenerator:
    def writeRequestList(self, scenarioList, totalSimulationTime, workingDir):
        typeList = []

        poiGroupDict = PoiTypeList().getGroups()

        self.workingDir = workingDir   

        poi2EdgeConverter = Poi2EdgeConverter()

        for scenario in scenarioList:
            print(scenario.fromPoiGroup)
            print(scenario.fromPoiAnySubGroup)
            print(scenario.fromPoiSubGroup)
            print(scenario.toPoiGroup)
            print(scenario.toPoiAnySubGroup)
            print(scenario.toPoiSubGroup)
            print(scenario.numberOfRequests)
            print(scenario.roundTrip)
            print(scenario.stayTime)
            print(scenario.normalDistributed)
            print(scenario.standardDeviation)

        fromSubGroupList = []
        toSubGroupList = []

        # first we have to find out which POIs are used in our scenarioList
        # and for them we have to create a List with all Edge Positions (and further information)
        for scenario in scenarioList:
            fromPoiGroup = scenario.fromPoiGroup.split(":")[1][1:]
            # if the checkbox "Any" is checked we have to add all subgroups to the typeList
            if scenario.fromPoiAnySubGroup:
                for subGroup in poiGroupDict[scenario.fromPoiGroup]:
                    fromPOI = fromPoiGroup + "." + subGroup
                    print(fromPOI)
                    if fromPOI not in typeList:
                        typeList.append(fromPOI)
                        fromSubGroupList.append(subGroup)
            else:
                fromPOI = fromPoiGroup + "." + scenario.fromPoiSubGroup
                if fromPOI not in typeList:
                    typeList.append(fromPOI)
                    fromSubGroupList.append(scenario.fromPoiSubGroup)

            # the same procedure for the target POI:
            toPoiGroup = scenario.toPoiGroup.split(":")[1][1:]
            if scenario.toPoiAnySubGroup:
                for subGroup in poiGroupDict[scenario.toPoiGroup]:
                    toPOI = toPoiGroup + "." + subGroup
                    print(toPOI)
                    if toPOI not in typeList:
                        typeList.append(toPOI)
                        toSubGroupList.append(subGroup)
            else:
                toPOI = toPoiGroup + "." + scenario.toPoiSubGroup
                if toPOI not in typeList:
                    typeList.append(toPOI)
                    toSubGroupList.append(scenario.toPoiSubGroup)

        # create EdgePositions.xml with all needed EdgePositions
        poi2EdgeConverter.convertPois2Edges(typeList,self.workingDir)

        # read the newly created EdgePositions.xml
        poiList = poi2EdgeConverter.readEdgeList()

        requestId = 0

        xml_output = ET.Element("requestlist")

        atLeastOneValidScenario = False
        # Now we create the scenarios
        for scenario in scenarioList:
            # fromPOI = scenario.fromPoiGroup.split(":")[1][1:]+"."+scenario.fromPoiSubGroup
            # toPOI = scenario.toPoiGroup.split(":")[1][1:]+"."+scenario.toPoiSubGroup

            fromPoiGroup = scenario.fromPoiGroup.split(":")[1][1:]
            toPoiGroup = scenario.toPoiGroup.split(":")[1][1:]

            # here we create subLists with the right types from which we can later pick POIs randomly
            fromSubList = []
            toSubList = []

            # here we iterate over all POIs which were read from EdgePositions.xml
            for poi in poiList:

                for sg in fromSubGroupList:
                    fromPOI = fromPoiGroup + "." + sg
                    if fromPOI in str(poi):
                        fromSubList.append(poi)

                for sg in toSubGroupList:
                    toPOI = toPoiGroup + "." + sg
                    if toPOI in str(poi):
                        toSubList.append(poi)

            if len(fromSubList) > 0 and len(toSubList) > 0:
                atLeastOneValidScenario = True
                numberOfRequests = int(scenario.numberOfRequests)
                print(
                    "create Requests for Scenario",
                    scenario.fromPoiGroup,
                    " -> ",
                    scenario.toPoiGroup,
                    ":",
                )
                for i in range(numberOfRequests):

                    # Here we pick a POI from the set fromSubList
                    pickFrom = random.choice(fromSubList)

                    # Here we pick a POI from the set toSubList
                    pickTo = random.choice(toSubList)

                    # to get the edgeId we remove the lane number at the end of the laneId
                    fromEdge = pickFrom["edge"]
                    toEdge = pickTo["edge"]

                    fromEdgePosition = pickFrom["position"]
                    toEdgePosition = pickTo["position"]

                    staytime = int(scenario.stayTime)

                    # here we try 10 times to find a suitable submitTime
                    counter = 0
                    while True:
                        counter += 1
                        submitTime = random.randint(0, int(totalSimulationTime))
                        if submitTime + staytime < int(totalSimulationTime):
                            break
                        if counter == 10:
                            submitTime = int(totalSimulationTime) - staytime
                            break

                    relatedID = ""
                    if scenario.roundTrip:
                        relatedID = str(requestId + 1)

                    # create Entry to the xml file for the current Request:
                    ET.SubElement(
                        xml_output,
                        "request",
                        id=str(requestId),
                        submitTime=str(submitTime),
                        fromPOI=pickFrom["type"],
                        fromEdge=fromEdge,
                        fromEdgePosition=fromEdgePosition,
                        toPOI=pickTo["type"],
                        toEdge=toEdge,
                        toEdgePosition=toEdgePosition,
                        relateId=relatedID,
                        fromDetails=str(pickFrom["details"]),
                        toDetails=str(pickTo["details"]),
                    )

                    # if the scenario contains a Roundtrip, we add a second Request and swap From and To:
                    if scenario.roundTrip:
                        # if the staytime should be normal distributed we have to calculate a new value for staytime
                        if scenario.normalDistributed:
                            # np.random.normal gives us a value according the normal distribution where loc = mean and scale = standard deviation
                            staytime = round(
                                abs(
                                    np.random.normal(
                                        loc=float(staytime),
                                        scale=float(scenario.standardDeviation),
                                        size=None,
                                    )
                                )
                            )
                        # here we add the stayTime to the previous submitTime -> this could be improved with randomization
                        submitTime = submitTime + staytime
                        relatedID = str(requestId)
                        requestId += 1
                        ET.SubElement(
                            xml_output,
                            "request",
                            id=str(requestId),
                            submitTime=str(submitTime),
                            fromPOI=pickTo["type"],
                            fromEdge=toEdge,
                            fromEdgePosition=toEdgePosition,
                            toPOI=pickFrom["type"],
                            toEdge=fromEdge,
                            toEdgePosition=fromEdgePosition,
                            relateId=relatedID,
                            fromDetails=str(pickFrom["details"]),
                            toDetails=str(pickTo["details"]),
                        )

                    requestId += 1
                    print("Request ", i + 1, "/", numberOfRequests, "was created")
            else:
                print(
                    "WARNING: for Scenario ",
                    scenario.fromPoiGroup,
                    " -> ",
                    scenario.toPoiGroup,
                    " no valid POIs could be found",
                )

        if atLeastOneValidScenario:
            tree = ET.ElementTree(xml_output)

            # formatting and writing the xml file
            tree.write(
                "./CustomerRequests.xml",
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )
            print("\nREADY! CustomerRequests.xml was created")
        else:
            print(
                "ERROR: CustomerRequests.xml could not be created because for no Scenario could any valid POIs could be found"
            )
