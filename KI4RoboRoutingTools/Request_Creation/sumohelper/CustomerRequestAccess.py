import xml.etree.ElementTree as xml
from datetime import datetime, timedelta

KEY_ID = "id"
KEY_SUBMIT_TIME = "submitTime"
KEY_FROM_POI = "fromPOI"
KEY_FROM_EDGE = "fromEdge"
KEY_FROM_EDGE_POSITION = "fromEdgePosition"
KEY_TO_POI = "toPOI"
KEY_TO_EDGE = "toEdge"
KEY_TO_EDGE_POSITION = "toEdgePosition"
KEY_RELATE_ID = "relateId"
KEY_FROM_DETAILS = "fromDetails"
KEY_TO_DETAILS = "toDetails"


class CustomerRequest:
    def __init__(self, submit_time_seconds: int, from_poi: str, from_edge: str, from_edge_pos: float, to_poi: str, to_edge: str, to_edge_pos: float):
        self.submit_time_seconds = submit_time_seconds
        self.from_poi = from_poi
        self.from_edge = from_edge
        self.from_edge_pos = from_edge_pos
        self.to_poi = to_poi
        self.to_edge = to_edge
        self.to_edge_pos = to_edge_pos
        self.id = -1

    def set_id(self, id: int):
        self.id = id

    def __eq__(self, other):
        if not isinstance(other, CustomerRequest):
            return NotImplemented
        return self.submit_time_seconds == other.submit_time_seconds and self.from_poi == other.from_poi \
               and self.from_edge == other.from_edge \
               and self.from_edge_pos == other.from_edge_pos \
               and self.to_poi == other.to_poi \
               and self.to_edge == other.to_edge \
               and self.to_edge_pos == other.to_edge_pos

    def __eq__(self, other):
        if not isinstance(other, CustomerRequest):
            return NotImplemented
        return self.submit_time_seconds == other.submit_time_seconds and self.from_poi == other.from_poi \
               and self.from_edge == other.from_edge \
               and self.from_edge_pos == other.from_edge_pos \
               and self.to_poi == other.to_poi \
               and self.to_edge == other.to_edge \
               and self.to_edge_pos == other.to_edge_pos


class CustomerRequestAccess:
    def __init__(self, start_datetime: datetime, sim_duration_seconds: int):
        self.__start_datetime = start_datetime
        self.__sim_duration_seconds = sim_duration_seconds
        self.__end_datetime = start_datetime + timedelta(seconds=self.__sim_duration_seconds)
        self.__requests = []
        self.__id_count = 0

    def add_request(self, request: CustomerRequest):
        if request.submit_time_seconds > self.__sim_duration_seconds:
            raise RuntimeError(f"ERROR: submit time of request ({request.submit_time_seconds}) "
                               f"exceeded simulation duration ({self.__sim_duration_seconds})")
        request.set_id(self.__id_count)
        self.__requests.append(request)
        self.__id_count += 1

    def get_all(self):
        return self.__requests

    def dump(self, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        root = xml.Element("requestlist")
        root.append(xml.Comment(
            f'### Start: {self.__start_datetime}, End: {self.__end_datetime}, Duration: {self.__sim_duration_seconds} s'))
        for req in self.__requests:
            el = xml.Element("request")
            el.set(KEY_ID, str(req.id))
            el.set(KEY_SUBMIT_TIME, str(req.submit_time_seconds))
            el.set(KEY_FROM_POI, req.from_poi)
            el.set(KEY_FROM_EDGE, req.from_edge)
            el.set(KEY_FROM_EDGE_POSITION, str(req.from_edge_pos))
            el.set(KEY_TO_POI, req.to_poi)
            el.set(KEY_TO_EDGE, req.to_edge)
            el.set(KEY_TO_EDGE_POSITION, str(req.to_edge_pos))
            el.set(KEY_RELATE_ID, "")
            el.set(KEY_FROM_DETAILS, "{}")
            el.set(KEY_TO_DETAILS, "{}")
            root.append(el)

        tree = xml.ElementTree(root)
        CustomerRequestAccess.__indent(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    @classmethod
    def read_from_file(cls, filename: str, format: str = "xml"):
        if format != "xml":
            raise RuntimeError(f"Unknown format: {format}")
        tree = xml.parse(filename)
        root = tree.getroot()
        requests = []
        for el in root:
            req = CustomerRequest(int(el.get(KEY_SUBMIT_TIME)), el.get(KEY_FROM_POI), el.get(KEY_FROM_EDGE),
                                  float(el.get(KEY_FROM_EDGE_POSITION)), el.get(KEY_TO_POI), el.get(KEY_TO_EDGE),
                                  float(el.get(KEY_TO_EDGE_POSITION)))
            requests.append(req)
        access = cls(datetime(year=1970, month=1, day=1), -1)
        access.__requests = requests
        return access

    def __indent(elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                CustomerRequestAccess.__indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def __len__(self):
        return len(self.__requests)
