#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: March 2021
# License: MIT License
# =============================================================================
# This script reduces SUMO Backround Traffic
# Usage: python3 trafficReducer.py -i routesLKW.xml -f 0.3
# This will reduce the number of routes of routesLKW.xml to 30% of the original
# =============================================================================

import os
import optparse
import sys
import lxml.etree as ET
import random


parser = optparse.OptionParser()
parser.add_option(
    "-i",
    "--input",
    action="store",
    dest="input_file",
    help="routeFile Input",
    default="routesPKW.xml",
)

parser.add_option(
    "-f",
    "--factor",
    action="store",
    dest="factor",
    help="reduction Factor",
    default=0.5,
)

options, args = parser.parse_args()


print("reducing route-File", options.input_file, "by factor", options.factor)

originalFile = options.input_file

try:
    routeTree = ET.parse(options.input_file)
except:
    print("The File ", options.input_file, "couldn't be read")
    sys.exit()

factor = float(options.factor)

if (factor < 0.01) or (float(factor) > 1):
    print("The reduction factor must be in a range between 0.01 and 1")
    sys.exit()

routeRoot = routeTree.getroot()

routeList = []

# read all routes
for route in routeRoot.findall("vehicle"):
    routeList.append(route)

totalNumberOfRoutes = len(routeList)
reducedNumberOfRoutes = int(totalNumberOfRoutes * factor)
print(
    "The total Number of Routes is reduced from",
    str(totalNumberOfRoutes),
    "to",
    str(reducedNumberOfRoutes),
)

xml_output = ET.Element("routes")

# write reduced set of random picked routes
for i in range(reducedNumberOfRoutes):
    route = routeList.pop(random.randrange(len(routeList)))
    vehicle = ET.SubElement(
        xml_output,
        "vehicle",
        id=route.attrib.get("id"),
        depart=route.attrib.get("depart"),
        type=route.attrib.get("type"),
        departLane=route.attrib.get("departLane"),
        departSpeed=route.attrib.get("departSpeed"),
        departPos=route.attrib.get("departPos"),
    )
    ET.SubElement(vehicle, "route", edges=route.findall("route")[0].attrib.get("edges"))

newFile = originalFile.split(".")[0] + "_" + str(int(factor * 100)) + "percent.xml"

tree = ET.ElementTree(xml_output)
tree.write(newFile, encoding="UTF-8", xml_declaration=True, pretty_print=True)
