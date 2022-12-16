import unittest
import os
from Python_Tools.Request_Creation.sumohelper.PoiEdgesAccess import PoiEdgesAccess, PoiEdge
from datetime import datetime, timedelta

SIMU_START_DATETIME = datetime(year=2014, month=10, day=10, hour=12, minute=0, second=0)
SIMU_END_DATETIME = datetime(year=2014, month=10, day=10, hour=12, minute=59, second=59)

LIST_POI_EDGES = [
    PoiEdge(poi_id=234,poi_tag="building.apartments",  edge_id="512", lane_pos=42.1, lane_idx="_0"),
    PoiEdge(poi_id=567, poi_tag="building.school", edge_id="512", lane_pos=0.0, lane_idx="_0")
]

class TestPoiEdgesAccess(unittest.TestCase):
    def test_something(self):
        creator = PoiEdgesAccess()
        creator.add_poi_edge(LIST_POI_EDGES[0])
        creator.add_poi_edge(LIST_POI_EDGES[1])
        # if file TestPoiEdgesAccess.xml exists, remove it
        if os.path.exists("TestPoiEdgesAccess.xml"):
            os.remove("TestPoiEdgesAccess.xml")
        creator.dump(filename="TestPoiEdgesAccess.xml", format="xml")
        reader = PoiEdgesAccess.read_from_file(filename="TestPoiEdgesAccess.xml", format="xml")
        self.assertListEqual(LIST_POI_EDGES, reader.get_all())


if __name__ == '__main__':
    unittest.main()
