import unittest
from datetime import datetime
from helper.RequestFilter import filter_by_datettime
import pandas as pd


class MyTestCase(unittest.TestCase):
    def test_filtering_by_date(self):
        start_date = datetime(2014, 10, 10, 12, 00, 00)
        end_date = datetime(2014, 10, 10, 12, 59, 59)
        data = {"STARTED_LOCAL": ["2014-10-10 11:37:28", "2014-10-10 12:37:28", "2014-10-10 13:37:28"]}
        df = pd.DataFrame(index=[0, 1, 2], data=data)
        print(df)
        df = filter_by_datettime(df=df, from_dt=start_date, to_dt=end_date)
        self.assertEqual(1, df.shape[0])

if __name__ == '__main__':
    unittest.main()
