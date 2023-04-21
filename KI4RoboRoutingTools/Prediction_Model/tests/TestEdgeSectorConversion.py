import unittest
from Python_Tools.Prediction_Model.edge_sector_converter import EdgeSectorConverter, EdgeCoordinates, Coordinates, SectorCoordinates, Sector
#from  import EdgeSectorConverter, EdgeCoordinates, Coordinates, SectorCoordinates, Sector

# create static list of SectorCoordinates
SECTOR_COORDS = SectorCoordinates()
SECTOR_COORDS.add_sector_coordinates(sector=Sector(0, 0), bbox=(0.0, 0.0, 5.0, 5.0), representative_edge="edge_in_sec_0_0")
SECTOR_COORDS.add_sector_coordinates(sector=Sector(0, 1), bbox=(5.0, 0.0, 10.0, 5.0), representative_edge="edge_in_sec_0_1")
SECTOR_COORDS.add_sector_coordinates(sector=Sector(1, 0), bbox=(0.0, 5.0, 5.0, 10.0), representative_edge="edge_in_sec_1_0")
SECTOR_COORDS.add_sector_coordinates(sector=Sector(1, 1), bbox=(5.0, 5.0, 10.0, 10.0), representative_edge="edge_in_sec_1_1")

# create static list of EdgeCoordinates
EDGE_COORDS = EdgeCoordinates()
EDGE_COORDS.add_edge_coordinates(edge_id="edge_in_sec_0_0", coords=Coordinates(2.5, 2.5))
EDGE_COORDS.add_edge_coordinates(edge_id="edge_in_sec_0_1", coords=Coordinates(2.5, 7.5))
EDGE_COORDS.add_edge_coordinates(edge_id="edge_in_sec_1_0", coords=Coordinates(7.5, 2.5))
EDGE_COORDS.add_edge_coordinates(edge_id="edge_in_sec_1_1", coords=Coordinates(7.5, 7.5))
# additional random ones from the POIs/Requests
EDGE_COORDS.add_edge_coordinates(edge_id="rand_edge_sec_0_0", coords=Coordinates(1.0, 1.0))
EDGE_COORDS.add_edge_coordinates(edge_id="rand_edge_sec_0_1", coords=Coordinates(1.0, 7.0))
EDGE_COORDS.add_edge_coordinates(edge_id="rand_edge_sec_1_0", coords=Coordinates(7.0, 1.0))
EDGE_COORDS.add_edge_coordinates(edge_id="rand_edge_sec_1_1", coords=Coordinates(7.0, 7.0))

NOT_CONTAINED_EDGE = "edge_not_contained"
OUT_OF_BOUNDS_SECTOR = Sector(2, 2)

class TestEdgeSectorConversion(unittest.TestCase):
    def test_to_sector(self):
        converter = EdgeSectorConverter(EDGE_COORDS, SECTOR_COORDS)
        self.assertEqual(converter.to_sector("edge_in_sec_0_0"), Sector(0, 0))
        self.assertEqual(converter.to_sector("edge_in_sec_0_1"), Sector(0, 1))
        self.assertEqual(converter.to_sector("edge_in_sec_1_0"), Sector(1, 0))
        self.assertEqual(converter.to_sector("edge_in_sec_1_1"), Sector(1, 1))
        self.assertEqual(converter.to_sector("rand_edge_sec_0_0"), Sector(0, 0))
        self.assertEqual(converter.to_sector("rand_edge_sec_0_1"), Sector(0, 1))
        self.assertEqual(converter.to_sector("rand_edge_sec_1_0"), Sector(1, 0))
        self.assertEqual(converter.to_sector("rand_edge_sec_1_1"), Sector(1, 1))
        with self.assertRaises(ValueError):
            converter.to_sector("not_existing_edge_id")

    def test_to_edge(self):
        converter = EdgeSectorConverter(EDGE_COORDS, SECTOR_COORDS)
        self.assertEqual(converter.to_edge(Sector(0, 0)), "edge_in_sec_0_0")
        self.assertEqual(converter.to_edge(Sector(0, 1)), "edge_in_sec_0_1")
        self.assertEqual(converter.to_edge(Sector(1, 0)), "edge_in_sec_1_0")
        self.assertEqual(converter.to_edge(Sector(1, 1)), "edge_in_sec_1_1")
        with self.assertRaises(ValueError):
            converter.to_edge(Sector(2, 2))

    def test_out_of_bounds_sector(self):
        converter = EdgeSectorConverter(EDGE_COORDS, SECTOR_COORDS)
        with self.assertRaises(ValueError):
            converter.to_edge(OUT_OF_BOUNDS_SECTOR)

    def test_not_contained_edge(self):
        converter = EdgeSectorConverter(EDGE_COORDS, SECTOR_COORDS)
        with self.assertRaises(ValueError):
            converter.to_sector(NOT_CONTAINED_EDGE)



if __name__ == '__main__':
    unittest.main()
