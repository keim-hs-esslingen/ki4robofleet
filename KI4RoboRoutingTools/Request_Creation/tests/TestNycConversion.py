import unittest
from KI4RoboRoutingTools.Request_Creation.helper.NycFormatConversionAndFilter import convert_nyc_to_sumo4av_format, filter_by_lat_long

class MyTestCase(unittest.TestCase):
    def test_something(self):
        df = convert_nyc_to_sumo4av_format("/home/steffen/Downloads/2016_05_06-08_NYC_trips.csv")
        df = filter_by_lat_long(df=df, long_min=-73.90, lat_min=40.67, long_max=-73.86, lat_max=40.80)
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
