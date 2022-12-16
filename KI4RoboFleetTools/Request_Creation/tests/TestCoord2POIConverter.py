import unittest
from sumohelper.Coord2POIConverter import findBestFittingPoi, get_default_poi

class MyTestCase(unittest.TestCase):
    def test_poi_amenity_success(self):
        poi_req, way_id = findBestFittingPoi(lat=47.6237946, long=-122.3568472, corr_algorithm="eqdistcircles", max_matching_distance_meters=0)
        self.assertEqual("amenity.fast_food", poi_req)

    def test_poi_no_direct_success(self):
        with self.assertRaises(RuntimeError):
            poi_req, way_id = findBestFittingPoi(lat=47.63981, long=-122.36755, corr_algorithm="eqdistcircles",
                                     max_matching_distance_meters=0)

    def test_poi_success_w_tolerance(self):
        poi_req, way_id = findBestFittingPoi(lat=47.63981, long=-122.36755, corr_algorithm="eqdistcircles",
                                     max_matching_distance_meters=50)
        self.assertEqual("amenity.place_of_worship", poi_req)

    def test_find_school(self):
        poi_req, way_id = findBestFittingPoi(lat=47.64073, long=-122.36558, corr_algorithm="eqdistcircles",
                                     max_matching_distance_meters=50)
        self.assertEqual("amenity.school", poi_req)

    def test_use_building_apartment_if_nothing_found(self):
        try:
            poi_req, way_id = findBestFittingPoi(lat=47.64225, long=-122.35917, corr_algorithm="eqdistcircles",
                                         max_matching_distance_meters=50)
        except RuntimeError as re:
            self.assertEqual("building.apartments", get_default_poi())

    def test_another_one(self):
        poi_req, way_id = findBestFittingPoi(lat=47.586557632797, long=-122.33581248283, corr_algorithm="normdist",
                                     max_matching_distance_meters=500)
        print(poi_req)

    def test_find_poi_id_around_poi(self):
        # direct success poi
        poi_req, way_id = findBestFittingPoi(lat=47.6237946, long=-122.3568472, corr_algorithm="eqdistcircles",
                                     max_matching_distance_meters=0)
        self.assertEqual("amenity.fast_food", poi_req)

if __name__ == '__main__':
    unittest.main()
