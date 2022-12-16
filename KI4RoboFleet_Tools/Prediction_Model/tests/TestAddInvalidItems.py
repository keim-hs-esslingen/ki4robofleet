import unittest
from Python_Tools.Prediction_Model.edge_sector_converter import EdgeSectorConverter, EdgeCoordinates, Coordinates, SectorCoordinates, Sector

# test wrong instatiation of Coordinates
class TestAddInvalidItems(unittest.TestCase):
    def test_sector_coordinates(self):
        sector_coords = SectorCoordinates()
        # add valid value
        sector_coords.add_sector_coordinates(sector=Sector(1, 2), bbox=(0.0, 0.0, 2.0, 2.0), representative_edge="edge_id")
        with self.assertRaises(ValueError):
            # duplicate sector
            sector_coords.add_sector_coordinates(sector=Sector(1, 2), bbox=(1.0, 1.0, 3.0, 3.0), representative_edge="edge_id2")
        with self.assertRaises(ValueError):
            # duplicate bbox
            sector_coords.add_sector_coordinates(sector=Sector(2, 3), bbox=(0.0, 0.0, 2.0, 2.0), representative_edge="edge_id3")
        with self.assertRaises(ValueError):
            # duplicate representative edge
            sector_coords.add_sector_coordinates(sector=Sector(3, 4), bbox=(1.0, 1.0, 3.0, 3.0), representative_edge="edge_id")
        # bad bbox
        with self.assertRaises(ValueError):
            sector_coords.add_sector_coordinates(sector=Sector(1, 5), bbox=(1.0, 2.0, 3.0), representative_edge="edge_id")
        # add second valid value
        sector_coords.add_sector_coordinates(sector=Sector(2, 3), bbox=(1.0, 1.0, 3.0, 3.0), representative_edge="edge_id2")

    def test_edge_coordinates_duplicate(self):
        edge_coords = EdgeCoordinates()
        edge_coords.add_edge_coordinates(edge_id="edge_id", coords=Coordinates(1.2, 2.5))
        edge_coords.add_edge_coordinates(edge_id="edge_id2", coords=Coordinates(1.2, 2.5))
        with self.assertRaises(ValueError):
            edge_coords.add_edge_coordinates(edge_id="edge_id", coords=Coordinates(1.5, 2.7))



if __name__ == '__main__':
    unittest.main()
