#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# The class XMLogger simplifies creating XML Log- and Resultfiles
# =============================================================================

import lxml.etree as ET
from datetime import datetime


def build_tree(parent, name, data):
    if type(data) is dict:
        new_element = ET.SubElement(parent, name)
        for k, v in data.items():
            build_tree(new_element, k, v)
    elif type(data) is list:
        for item in data:
            new_element = ET.SubElement(parent, name)
            build_tree(new_element, "value", item)
    else:
        # add attributes to the current element
        parent.set(name, str(data))


DEFAULT_ROOT = "logbook"
DEFAULT_ENTRY = "log"


class XMLogger:
    def __init__(self):
        self.currentParamSet = ET.Element(DEFAULT_ROOT)

    def write(self, filename=None):
        if not filename:
            filename = datetime.now().strftime("log_%Y_%m_%d-%H_%M.xml")
        self.writeXmlFile(filename)

    def addEntry(self, name, data):
        build_tree(self.currentParamSet, name, data)

    def writeXmlFile(self, filename):
        tree = ET.ElementTree(self.currentParamSet)

        # formatting and writing the xml file
        tree.write(filename, encoding="UTF-8", xml_declaration=True, pretty_print=True)
        print("The Logfile", filename, "was created")
        self.currentParamSet = ET.Element(DEFAULT_ROOT)


G_logger = None


def write_log(filename=None):
    global G_logger
    if G_logger:
        G_logger.write(filename)


def xlog(**kwargs):
    global G_logger
    if not G_logger:
        G_logger = XMLogger()
    if "name" in kwargs:
        name = kwargs["name"]
        del kwargs["name"]
    else:
        name = DEFAULT_ENTRY
    G_logger.addEntry(name, kwargs)


if __name__ == "__main__":
    xlog(name="session", time=123, num_of_vehicles=50)
    xlog(time=123, num_of_vehicles=50)
    xlog(t=1, x=2, subset={"t": 3, "a": 15})
    xlog(t=2, x=2, arr=[1, 2, 3, [4, 3, {"test": 123}]])
    write_log("test.xml")
