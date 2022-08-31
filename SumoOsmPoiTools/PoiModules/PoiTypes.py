13#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: November 2020
# License: MIT License
# =============================================================================
# This script extracts POI- Types from osm.poly.xml and counts the occurrence
# of each POI and finally a CSV file is written which can be used to make
# Statistics for the available POI Types
# =============================================================================


import lxml.etree as ET
import os
import csv


class PoiTypeList:
    pois = {}
    poiGroup = {}

    def __init__(self, osmPolyFile = "osm.poly.xml" ):
        self.osmPolyFile = osmPolyFile
        try:
            polyTree = ET.parse(osmPolyFile)
            polyRoot = polyTree.getroot()
            print("Import ",osmPolyFile)
            # read the <poly> - Tags:
            for poly in polyRoot.findall("poly"):
                polyType = poly.attrib.get("type")
                if "POLY: " + polyType in self.pois:
                    self.pois["POLY: " + polyType] += 1
                else:
                    self.pois["POLY: " + polyType] = 1

            # read the <poi> - Tags:
            for poi in polyRoot.findall("poi"):
                poiType = poi.attrib.get("type")
                if "POI: " + poiType in self.pois:
                    self.pois["POI: " + poiType] += 1
                else:
                    self.pois["POI: " + poiType] = 1
            print("READY!")
        except:
            print(
                "An Error has occurred: please check if the selected 'osm.poly.xml' file is flawless"
            )

        # create a dictionary  key: POI Group (eg. shop) value: list of SubGroups (eg. supermarket, florist, bakery,...)
        for poiType in self.pois.keys():
            pGroup = poiType.split(".")[0]
            pSubGroup = poiType.split(".")[1]

            if pGroup not in self.poiGroup.keys():
                self.poiGroup[pGroup] = []
                self.poiGroup[pGroup].append(pSubGroup)
            else:
                if pSubGroup not in self.poiGroup[pGroup]:
                    self.poiGroup[pGroup].append(pSubGroup)

    def getList(self):
        return self.pois

    def getSortedList(self):
        return sorted(self.pois)

    def getGroups(self):
        return self.poiGroup

    def writeStatistics(self, workingDir):
        with open(workingDir+"/PoiStatistics.csv", mode="w") as csv_file:
            fieldnames = ["poiType", "name", "occurrence"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for poi in sorted(self.pois):
                poiType = poi.split(":")[0].lower()
                name = poi.split(":")[1][1:]
                writer.writerow(
                    {
                        "poiType": poiType,
                        "name": name,
                        "occurrence": str(self.pois[poi]),
                    }
                )

    def applyViewSettings(self, keepOriginalPolys, keepOriginalPOIs, osmPolyFile, viewSettingFile):
        self.osmPolyFile = osmPolyFile
        print("Params:")
        print(" keepOriginalPolys: ", keepOriginalPolys)
        print(" keepOriginalPOIs: ", keepOriginalPOIs)

        try:

            print("Reading ", self.osmPolyFile)

            polyTree = ET.parse(self.osmPolyFile)
            polyRoot = polyTree.getroot()

            print("Reading " + viewSettingFile)

            settingsTree = ET.parse(viewSettingFile)
            settingsRoot = settingsTree.getroot()

            # read the color (and other) settings from POI_Settings.xml and write them to a dictionary

            polySettings = {}
            for setting in settingsRoot.findall("poly"):
                polySettings[setting.attrib.get("type")] = [
                    setting.attrib.get("color"),
                    setting.attrib.get("fill"),
                    setting.attrib.get("layer"),
                ]

            poiSettings = {}

            for setting in settingsRoot.findall("poi"):
                poiSettings[setting.attrib.get("type")] = [
                    setting.attrib.get("color"),
                    setting.attrib.get("layer"),
                ]

            xml_output = ET.Element("additional")

            pois = {}
            # read the <poly> - Tags:
            for poly in polyRoot.findall("poly"):
                polyType = poly.attrib.get("type")

                if polyType in polySettings:
                    ET.SubElement(
                        xml_output,
                        "poly",
                        id=poly.attrib.get("id"),
                        type=polyType,
                        color=polySettings[polyType][0],
                        fill=polySettings[polyType][1],
                        layer=polySettings[polyType][2],
                        shape=poly.attrib.get("shape"),
                    )
                else:
                    if keepOriginalPolys:
                        ET.SubElement(
                            xml_output,
                            "poly",
                            id=poly.attrib.get("id"),
                            type=polyType,
                            color=poly.attrib.get("color"),
                            fill=poly.attrib.get("fill"),
                            layer=poly.attrib.get("layer"),
                            shape=poly.attrib.get("shape"),
                        )
            # read the <poi> - Tags:
            for poi in polyRoot.findall("poi"):
                poiType = poi.attrib.get("type")
                if poiType in poiSettings:
                    ET.SubElement(
                        xml_output,
                        "poi",
                        id=poi.attrib.get("id"),
                        type=poiType,
                        color=poiSettings[poiType][0],
                        layer=poiSettings[poiType][1],
                        x=poi.attrib.get("x"),
                        y=poi.attrib.get("y"),
                    )
                else:
                    if keepOriginalPOIs:
                        ET.SubElement(
                            xml_output,
                            "poi",
                            id=poi.attrib.get("id"),
                            type=poiType,
                            color=poi.attrib.get("color"),
                            layer=poi.attrib.get("layer"),
                            x=poi.attrib.get("x"),
                            y=poi.attrib.get("y"),
                        )

            tree = ET.ElementTree(xml_output)

            # formatting and writing the xml file
            outputFile =  os.path.dirname(osmPolyFile)+"/osm.poly.customized.xml"
            print("Writing ", outputFile)
            tree.write(
                outputFile,
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )

            print("READY!!!")

        except:
            print(
                "An Error has occurred: please check if the input files are valid xml files"
            )
