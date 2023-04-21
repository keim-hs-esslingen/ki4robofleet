import xml.etree.ElementTree as xml
from datetime import datetime, timedelta

KEY_ROW = "row"
KEY_COL = "col"
KEY_BBOX = "bbox"
KEY_REPRESENTATIVE_EDGE = "representative_edge"


class SectorCoord:
    def __init__(self, row: int, col: int, bbox: list, representative_edge: str):
        self.row = row
        self.col = col
        # check if bbox is a list of 4 floats
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(x, float) for x in bbox):
            raise RuntimeError(f"bbox must be a list of 4 floats, but is {bbox}")
        # check if 1. and 3. element of bbox are in [-180, 180] and 2. and 4. element of bbox are in [-90, 90]
        if not (-180 <= bbox[0] <= 180 and -180 <= bbox[2] <= 180 and -90 <= bbox[1] <= 90 and -90 <= bbox[3] <= 90):
            raise RuntimeError(f"bbox must be in the form [lat_min, lon_min, lat_max, lon_max], but is {bbox}")
        # 1. and 3. element and 2. and 4. element must not be equal
        if bbox[0] == bbox[2] or bbox[1] == bbox[3]:
            raise RuntimeError(f"bbox must be in the form [lat_min, lon_min, lat_max, lon_max], but is {bbox}")
        self.bbox = bbox
        # check if representative_edge is a string and not empty
        if not isinstance(representative_edge, str) or len(representative_edge) == 0:
            raise RuntimeError(f"representative_edge must be a non-empty string, but is {representative_edge}")
        self.representative_edge = representative_edge

    def __eq__(self, other):
        if not isinstance(other, SectorCoord):
            return NotImplemented
        return self.row == other.row and self.col == other.col \
               and self.bbox == other.bbox \
               and self.representative_edge == other.representative_edge



class SectorCoordsAccess:
    def __init__(self):
        self.__sector_coords = []

    def add_sector_coord(self, sector_coord: SectorCoord):
        self.__sector_coords.append(sector_coord)

    def get_all(self):
        return self.__sector_coords

    def dump(self, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        root = xml.Element("sector_coord_collection")
        for sector_coord in self.__sector_coords:
            el = xml.Element("sector")
            el.set(KEY_ROW, str(sector_coord.row))
            el.set(KEY_COL, str(sector_coord.col))
            el.set(KEY_BBOX, str(sector_coord.bbox))
            el.set(KEY_REPRESENTATIVE_EDGE, str(sector_coord.representative_edge))
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
        sector_coords_access = SectorCoordsAccess()
        for el in root:
            row = int(el.get(KEY_ROW))
            col = int(el.get(KEY_COL))
            bbox = eval(el.get(KEY_BBOX))
            representative_edge = el.get(KEY_REPRESENTATIVE_EDGE)
            sector_coord = SectorCoord(row, col, bbox, representative_edge)
            sector_coords_access.add_sector_coord(sector_coord)
        return sector_coords_access

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
        return len(self.__sector_coords)