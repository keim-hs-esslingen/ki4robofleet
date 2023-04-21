import unittest
import os
from Python_Tools.Request_Creation.sumohelper.SectorCoordsAccess import SectorCoordsAccess, SectorCoord


SECTOR_COORDS_LIST = [
    SectorCoord(row=0, col=0, bbox=[-180.0, -90.0, 180.0, 90.0], representative_edge="12345678#"),
    SectorCoord(row=1, col=1, bbox=[0.0, 0.0, 0.1, 0.1], representative_edge="-15362634#2")
]

class TestSectorCoordsAccess(unittest.TestCase):
    def test_something(self):
        creator = SectorCoordsAccess()
        creator.add_sector_coord(SECTOR_COORDS_LIST[0])
        creator.add_sector_coord(SECTOR_COORDS_LIST[1])
        # if file TestSectorCoordsAccess.xml exists, remove it
        if os.path.exists("TestSectorCoordsAccess.xml"):
            os.remove("TestSectorCoordsAccess.xml")
        creator.dump(filename="TestSectorCoordsAccess.xml", format="xml")
        reader = SectorCoordsAccess.read_from_file(filename="TestSectorCoordsAccess.xml", format="xml")
        self.assertListEqual(SECTOR_COORDS_LIST, reader.get_all())


if __name__ == '__main__':
    unittest.main()
