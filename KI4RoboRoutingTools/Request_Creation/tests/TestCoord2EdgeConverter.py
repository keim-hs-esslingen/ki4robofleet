import unittest
import sys
import argparse
from sumohelper.Coord2EdgeConverter import EdgeFinder

class Coord2EdgeConverterTest(unittest.TestCase):
    SUMO_CONFIG = "../../../../Seattle_OSM/osm.sumocfg"

    def __init__(self, sd: str, *args, **kwargs):
        super(Coord2EdgeConverterTest, self).__init__(*args, **kwargs)
        # Init TraCI
        self.converter = EdgeFinder(Coord2EdgeConverterTest.SUMO_CONFIG)
        #  Address: 619, 5th Avenue West, Uptown, Belltown, Seattle, King County, Washington, 98119, Vereinigte Staaten von Amerika
        self.seattle_perfect_fit = {"edges_list": ["6445226", "242501648", "6469959"], "lat": 47.62529,
                                    "long": -122.36356, "max_dist_meters": 50}
        #  Grand Canyon, AZ 36.0997623,-112.1212394
        self.grand_canyon_no_match = {"edges_list": ["6445226", "242501648", "6469959"], "lat": 36.0997623,
                                      "long": -112.1212394, "max_dist_meters": 500}
        #  Match with correction possible
        self.match_w_corr = {"edges_list": ["-332223485#1"], "lat": 47.598331577084,
                             "long": -122.32762094688, "max_dist_meters": 100}
        self.empty_edges = []

        pass

    def test_perfect_fit_no_correction(self):
        # Find the perfect fitting edge
        edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.seattle_perfect_fit["lat"],
                                                                        long=self.seattle_perfect_fit["lat"],
                                                                        edges_list=self.seattle_perfect_fit[
                                                                            "edges_list"],
                                                                        allow_correction=False)
        self.assertTrue(edgeId in self.seattle_perfect_fit["edges_list"])

    def test_no_fit_wo_correction(self):
        # Find no fit
        with self.assertRaises(RuntimeError):
            edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.match_w_corr["lat"],
                                                                            long=self.match_w_corr["lat"],
                                                                            edges_list=self.match_w_corr[
                                                                                "edges_list"],
                                                                            allow_correction=False)

    def test_eqdistcircles_algorithm(self):
        # Find the perfect fitting edge
        edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.seattle_perfect_fit["lat"],
                                                                        long=self.seattle_perfect_fit["lat"],
                                                                        edges_list=self.seattle_perfect_fit[
                                                                            "edges_list"], allow_correction=True,
                                                                        corr_algorithm="eqdistcircles",
                                                                        max_matching_distance_meters=
                                                                        self.seattle_perfect_fit["max_dist_meters"])
        self.assertTrue(edgeId in self.seattle_perfect_fit["edges_list"])

        # Raise exception not finding grand canyon as edge
        with self.assertRaises(RuntimeError):
            edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.grand_canyon_no_match["lat"],
                                                                            long=self.grand_canyon_no_match["lat"],
                                                                            edges_list=self.grand_canyon_no_match[
                                                                                "edges_list"], allow_correction=True,
                                                                            corr_algorithm="eqdistcircles",
                                                                            max_matching_distance_meters=
                                                                            self.grand_canyon_no_match[
                                                                                "max_dist_meters"])
        edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.match_w_corr["lat"],
                                                                        long=self.match_w_corr["lat"],
                                                                        edges_list=self.match_w_corr[
                                                                            "edges_list"],
                                                                        allow_correction=True,
                                                                        corr_algorithm="eqdistcircles",
                                                                        max_matching_distance_meters=
                                                                        self.match_w_corr[
                                                                            "max_dist_meters"])
        self.assertTrue(edgeId in self.match_w_corr["edges_list"])

    def test_normdist_algorithm(self):
        edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.seattle_perfect_fit["lat"],
                                                                        long=self.seattle_perfect_fit["lat"],
                                                                        edges_list=self.seattle_perfect_fit[
                                                                            "edges_list"], allow_correction=True,
                                                                        corr_algorithm="normdist",
                                                                        max_matching_distance_meters=
                                                                        self.seattle_perfect_fit["max_dist_meters"])
        self.assertTrue(edgeId in self.seattle_perfect_fit["edges_list"])
        # Raise exception not finding grand canyon as edge
        with self.assertRaises(RuntimeError):
            edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.grand_canyon_no_match["lat"],
                                                                            long=self.grand_canyon_no_match["lat"],
                                                                            edges_list=self.grand_canyon_no_match[
                                                                                "edges_list"], allow_correction=True,
                                                                            corr_algorithm="normdist",
                                                                            max_matching_distance_meters=
                                                                            self.grand_canyon_no_match[
                                                                                "max_dist_meters"])
        edgeId, lane_pos, lane_idx = self.converter.findBestFittingEdge(lat=self.match_w_corr["lat"],
                                                                        long=self.match_w_corr["lat"],
                                                                        edges_list=self.match_w_corr[
                                                                            "edges_list"],
                                                                        allow_correction=True,
                                                                        corr_algorithm="normdist",
                                                                        max_matching_distance_meters=
                                                                        self.match_w_corr[
                                                                            "max_dist_meters"])
        self.assertTrue(edgeId in self.match_w_corr["edges_list"])


if __name__ == '__main__':
    unittest.main()
