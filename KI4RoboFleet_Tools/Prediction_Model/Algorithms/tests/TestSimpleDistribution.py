import unittest
import pandas as pd
from Python_Tools.Prediction_Model.Algorithms.algorithm_factory import AlgorithmFactory
from Python_Tools.Prediction_Model.edge_coordinates import EdgeCoordinates, Coordinates
from Python_Tools.Prediction_Model.sector_coordinates import SectorCoordinates, Sector
from Python_Tools.Prediction_Model.TrainingData.training_data import TrainingData

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
# create initial vehicle distribution as dict with key vid and value rand edge
INITIAL_VEHICLE_DISTRIBUTION = {
    "vid_0": "rand_edge_sec_0_0",
    "vid_1": "rand_edge_sec_0_1",
    "vid_2": "rand_edge_sec_1_0",
    "vid_3": "rand_edge_sec_1_1"
}
NOT_EXISTING_EDGE = "not_existing_edge"
NOT_EXISTING_VEHICLE = "not_existing_vehicle"
# create static target distribution as Training Data
T1_DATA = {
    "WEEKDAY": [0, 0, 0, 0],
    "HOUR": [2, 2, 2, 2],
    "ROW": [0, 0, 1, 1],
    "COL": [0, 1, 0, 1],
    "REQUESTS": [5, 5, 5, 5]  # 5 requests per sector (equal distribution)
}
TRAINING_DATA = TrainingData.from_weekday_hour_df(pd.DataFrame(data=T1_DATA, columns=["WEEKDAY", "HOUR", "ROW", "COL", "REQUESTS"]))

class TestSimpleDistributionAlgorithm(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        factory = AlgorithmFactory(edge_coordinates=EDGE_COORDS,
                                   sector_coordinates=SECTOR_COORDS,
                                   init_vehicle_pos_edges=INITIAL_VEHICLE_DISTRIBUTION,
                                   training_data=TRAINING_DATA)
        self.algorithm = factory.get_algorithm(algorithm_name="simple_distribution")

    def test_with_initial_distribution(self):
        # algorithm should return same result for all vids
        self.assertEqual(self.algorithm.get_edge("vid_0"), None)
        self.assertEqual(self.algorithm.get_edge("vid_1"), None)
        self.assertEqual(self.algorithm.get_edge("vid_2"), None)
        self.assertEqual(self.algorithm.get_edge("vid_3"), None)

    def test_valid_scenario(self):
        # move vid_0 to sector (1,1)
        self.algorithm.push_edge("vid_0", "edge_in_sec_1_1", time=0)
        # current distribution is now ((0.00, 0.25), (0.25, 0.50)
        # --> so a arbitrary vid should be moved to (0, 0) to balance distribution again, vid_2 is asking...
        self.assertEqual(self.algorithm.get_edge("vid_2"), "edge_in_sec_0_0")
        # vid_2 moves to 0_0 and pushes its edge (update edge)
        self.algorithm.push_edge("vid_2", "edge_in_sec_0_0", time=0)
        # meanwhile vid_3 moves to 0_1 so current distribution will be ((0.25, 0.50), (0.00, 0.25))
        self.algorithm.push_edge("vid_3", "edge_in_sec_0_1", time=0)
        # now vid_1 should be moved to 1_0 to balance distribution again
        self.assertEqual(self.algorithm.get_edge("vid_1"), "edge_in_sec_1_0")
        # vid_1 moves to 1_0 and pushes its edge (update edge)
        self.algorithm.push_edge("vid_1", "edge_in_sec_1_0", time=0)
        self.assertEqual(self.algorithm.get_edge("vid_0"), None)

    def test_threshold_with_new_vehicles(self):
        # new vehicle is added to simulation
        # algorithm should still return None, because no sector is underserved, there are too many vehicles
        self.algorithm.push_edge("vid_4", "edge_in_sec_0_0", time=0)
        self.assertEqual(self.algorithm.get_edge("vid_0"), None)
        self.algorithm.push_edge("vid_5", "edge_in_sec_0_1", time=0)
        self.assertEqual(self.algorithm.get_edge("vid_0"), None)
        self.algorithm.push_edge("vid_6", "edge_in_sec_1_0", time=0)
        self.assertEqual(self.algorithm.get_edge("vid_0"), None)
        # if one more vehicle is added to sec_0_0, then there will be a underserved sector
        self.algorithm.push_edge("vid_7", "edge_in_sec_0_0", time=0)
        self.assertEqual(self.algorithm.get_edge("vid_0"), "edge_in_sec_1_1")

    def test_invalid_parameters(self):
        # no violation, model will not be updated
        with self.assertRaises(ValueError):
            self.algorithm.push_edge("vid_0", NOT_EXISTING_EDGE, time=0)
        # no violation, this algorithm does not care about vids
        self.algorithm.get_edge(NOT_EXISTING_VEHICLE)

    def __del__(self):
        print("WARNING: So far only tested with 4 vehicles and 4 sectors and static + equal distribution!")

if __name__ == '__main__':
    unittest.main()



