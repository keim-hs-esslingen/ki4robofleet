import unittest
import os
from Python_Tools.Request_Creation.sumohelper.EdgeCoordsAccess import EdgeCoordsAccess, EdgeCoord

EDGE_COORDS_LIST = [
    EdgeCoord(edge_id="12345678#", lat=23.0512451, long=-122.0521243),
    EdgeCoord(edge_id="-15362634#2", lat=0.00000, long=180.00000)
]
class TestEdgeCoordsAccess(unittest.TestCase):
    def test_something(self):
        creator = EdgeCoordsAccess()
        creator.add_edge_coord(EDGE_COORDS_LIST[0])
        creator.add_edge_coord(EDGE_COORDS_LIST[1])
        # if file TestEdgeCoordsAccess.xml exists, remove it
        if os.path.exists("TestEdgeCoordsAccess.xml"):
            os.remove("TestEdgeCoordsAccess.xml")
        creator.dump(filename="TestEdgeCoordsAccess.xml", format="xml")
        reader = EdgeCoordsAccess.read_from_file(filename="TestEdgeCoordsAccess.xml", format="xml")
        self.assertListEqual(EDGE_COORDS_LIST, reader.get_all())



if __name__ == '__main__':
    unittest.main()
