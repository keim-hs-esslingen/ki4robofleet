import xml.etree.ElementTree as xml
from datetime import datetime, timedelta

KEY_ID = "id"
KEY_POI_TYPE = "type"
KEY_POI_EDGE_ID = "edge_id"
KEY_POI_LANE_POS = "lane_position"
KEY_POI_LANE_IDX = "lane_index"


class PoiEdge:
    def __init__(self, poi_id: int, poi_tag: str, edge_id: str, lane_pos: float, lane_idx: str):
        self.poi_id = poi_id
        self.poi_tag = poi_tag
        self.edge_id = edge_id
        self.lane_pos = lane_pos
        self.lane_idx = lane_idx

    def __eq__(self, other):
        if not isinstance(other, PoiEdge):
            return NotImplemented
        return self.poi_id == other.poi_id and self.poi_tag == other.poi_tag \
               and self.edge_id == other.edge_id \
               and self.lane_pos == other.lane_pos \
               and self.lane_idx == other.lane_idx


class PoiEdgesAccess:
    def __init__(self):
        self.__poi_edges = []

    def add_poi_edge(self, poi_edge: PoiEdge):
        self.__poi_edges.append(poi_edge)

    def get_all(self):
        return self.__poi_edges

    def dump(self, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        root = xml.Element("poi_collection")
        for poi_edge in self.__poi_edges:
            el = xml.Element("poi")
            el.set(KEY_ID, str(poi_edge.poi_id))
            el.set(KEY_POI_TYPE, poi_edge.poi_tag)
            el.set(KEY_POI_EDGE_ID, poi_edge.edge_id)
            el.set(KEY_POI_LANE_POS, str(poi_edge.lane_pos))
            el.set(KEY_POI_LANE_IDX, poi_edge.lane_idx)
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
        poi_edges_access = PoiEdgesAccess()
        for poi in root:
            poi_id = int(poi.get(KEY_ID))
            poi_tag = poi.get(KEY_POI_TYPE)
            edge_id = poi.get(KEY_POI_EDGE_ID)
            lane_pos = float(poi.get(KEY_POI_LANE_POS))
            lane_idx = poi.get(KEY_POI_LANE_IDX)
            poi_edges_access.add_poi_edge(PoiEdge(poi_id, poi_tag, edge_id, lane_pos, lane_idx))
        return poi_edges_access

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
