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
    def __init__(self, net_path: str):
        try:
            netTree = ET.parse(net_path)
            self.netRoot = netTree.getroot()
        except:
            print("An Error has occurred: please check if a valid 'osm.net.xml' file is in the current directory")
            self.netRoot = None

    def __check_init(self):
        if self.netRoot is None:
            raise("Initialization of NetFilter failed. Reinit class!")

    def filter(self, filters: dict={}, distinct: bool=False) -> list:
        self.__check_init()
        edges = self.netRoot.findall("edge")
        edges_out = []
        for edge in edges:
            eid = edge.attrib.get("id")
            # edgeIds with ":" cause problems because they are intersections or are not reachable by cars
            if ":" in eid:
                continue

            lanes = edge.findall("lane")
            for lane in lanes:
                match = True
                for fil, fil_val in filters.items():
                    try:
                        value = lane.attrib.get(fil)
                        if fil_val == "NOT_EMPTY" and len(value) > 0:
                            continue
                        if value != filters[fil]:
                            match = False
                            break
                    except:
                        match = False
                        break
                if match:
                    edges_out.append(eid)
                    break
        return edges_out
