import xml.etree.ElementTree as xml
from datetime import datetime, timedelta

KEY_EDGE_ID = "edge_id"
KEY_LAT = "lat"
KEY_LONG = "long"


class EdgeCoord:
    def __init__(self, edge_id: str, lat: float, long: float):
        self.edge_id = edge_id
        self.lat = lat
        self.long = long

    def __eq__(self, other):
        if not isinstance(other, EdgeCoord):
            return NotImplemented
        return self.edge_id == other.edge_id and self.lat == other.lat and self.long == other.long


class EdgeCoordsAccess:
    def __init__(self):
        self.__edge_coords = []

    def add_edge_coord(self, edge_coord: EdgeCoord):
        self.__edge_coords.append(edge_coord)

    def get_all(self):
        return self.__edge_coords

    def dump(self, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        root = xml.Element("edge_coord_collection")
        for edge_coord in self.__edge_coords:
            el = xml.Element("edge")
            el.set(KEY_EDGE_ID, str(edge_coord.edge_id))
            el.set(KEY_LAT, str(edge_coord.lat))
            el.set(KEY_LONG, str(edge_coord.long))
            root.append(el)

        tree = xml.ElementTree(root)
        self.__indent(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    @classmethod
    def read_from_file(cls, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        tree = xml.parse(filename)
        root = tree.getroot()
        edge_coords_access = EdgeCoordsAccess()
        for edge in root:
            edge_id = edge.get(KEY_EDGE_ID)
            lat = float(edge.get(KEY_LAT))
            long = float(edge.get(KEY_LONG))
            edge_coords_access.add_edge_coord(EdgeCoord(edge_id, lat, long))
        return edge_coords_access

    def __indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.__indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def __len__(self):
        return len(self.__edge_coords)
