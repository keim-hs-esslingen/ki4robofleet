import unittest
from Python_Tools.Prediction_Model.TrainingData.training_data import TrainingData
import pandas as pd

T1_DATA = {
    "WEEKDAY": [0, 0, 0, 0],
    "HOUR": [2, 2, 2, 2],
    "ROW": [0, 0, 1, 1],
    "COL": [0, 1, 0, 1],
    "REQUESTS": [0, 5, 10, 10]
}

T2_DATA = {
    "WEEKDAY": [0, 0, 0, 0],
    "HOUR": [3, 3, 3, 3],
    "ROW": [0, 0, 1, 1],
    "COL": [0, 1, 0, 1],
    "REQUESTS": [0, 5, 15, 20]
}

T1_REL_TIME_SECONDS = 2 * 3600
T2_REL_TIME_SECONDS = 3 * 3600
T12_REL_TIME_SECONDS = 2.5 * 3600

T1_DISTRIBUTION = pd.DataFrame(data=T1_DATA, columns=["WEEKDAY", "HOUR", "ROW", "COL", "REQUESTS"])
T2_DISTRIBUTION = pd.DataFrame(data=T2_DATA, columns=["WEEKDAY", "HOUR", "ROW", "COL", "REQUESTS"])
T12_REQUESTS = pd.Series([0, 5, 12.5, 15], name="REQUESTS")
T12_REQUESTS_NORM = pd.Series([0, 0.25, 0.625, 0.75], name="REQUESTS")

T1_AS_RELA_TIME = T1_DISTRIBUTION.copy()
T1_AS_RELA_TIME["REL_TIME_SECONDS"] = T1_DISTRIBUTION.apply(lambda row: (row['WEEKDAY'] * 24 + row['HOUR']) * 3600, axis=1)
T1_AS_RELA_TIME.drop(columns=['WEEKDAY', 'HOUR'], inplace=True)

T0_REQUESTS = pd.Series([0, 5, 10, 10], name="REQUESTS")  # expect T1_REQUESTS

T2_AS_RELA_TIME = T2_DISTRIBUTION.copy()
T2_AS_RELA_TIME["REL_TIME_SECONDS"] = T2_DISTRIBUTION.apply(lambda row: (row['WEEKDAY'] * 24 + row['HOUR']) * 3600, axis=1)
T2_AS_RELA_TIME.drop(columns=['WEEKDAY', 'HOUR'], inplace=True)

T3_REQUESTS = pd.Series([0, 5, 15, 20], name="REQUESTS")  # expect T2_REQUESTS

class TestTrainingData(unittest.TestCase):
    def test_get_none_interpolated_none_norm(self):
        print(self._testMethodName)
        training_data = TrainingData.from_weekday_hour_df(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                                          abs_start_dt=None, normalize_cols=None)
        t1_record = training_data.get_record(T1_REL_TIME_SECONDS, interpolated=False)
        print(t1_record)
        self.assertTrue(T1_AS_RELA_TIME.equals(t1_record))
        t2_record = training_data.get_record(T2_REL_TIME_SECONDS, interpolated=False)
        print(t2_record)
        self.assertTrue(T2_AS_RELA_TIME.equals(t2_record))

    def test_get_interpolated_none_norm(self):
        # print test name
        print(self._testMethodName)
        training_data = TrainingData.from_weekday_hour_df(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                                          abs_start_dt=None, normalize_cols=None)
        t12_record = training_data.get_record(T12_REL_TIME_SECONDS, interpolated=True)
        print(t12_record)
        self.assertTrue(T12_REQUESTS.equals(t12_record['REQUESTS']))
        self.assertTrue(len(t12_record['REL_TIME_SECONDS'] == T12_REL_TIME_SECONDS) == 4)

    def test_get_interpolated_norm(self):
        # print test name
        print(self._testMethodName)
        training_data = TrainingData.from_weekday_hour_df(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                                          abs_start_dt=None, normalize_cols=['REQUESTS'])
        t12_record = training_data.get_record(T12_REL_TIME_SECONDS, interpolated=True)
        print(t12_record)
        self.assertTrue(T12_REQUESTS_NORM.equals(t12_record['REQUESTS']))
        self.assertTrue(len(t12_record['REL_TIME_SECONDS'] == T12_REL_TIME_SECONDS) == 4)

    def test_t0_interpolated(self):
        # print test name
        print(self._testMethodName)
        training_data = TrainingData.from_weekday_hour_df(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                                          abs_start_dt=None, normalize_cols=None)
        t0_record = training_data.get_record(0, interpolated=True)
        print(t0_record)
        self.assertTrue(T0_REQUESTS.equals(t0_record['REQUESTS']))
        self.assertTrue(len(t0_record['REL_TIME_SECONDS'] == 0) == 4)

    def test_t3_interpolated(self):
        # print test name
        print(self._testMethodName)
        training_data = TrainingData.from_weekday_hour_df(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                                          abs_start_dt=None, normalize_cols=None)
        t3_record = training_data.get_record(T2_REL_TIME_SECONDS + 1, interpolated=True)
        print(t3_record)
        self.assertTrue(T3_REQUESTS.equals(t3_record['REQUESTS']))
        self.assertTrue(len(t3_record['REL_TIME_SECONDS'] == T2_REL_TIME_SECONDS + 1) == 4)

    def test_pass_empty_df(self):
        # print test name
        print(self._testMethodName)
        with self.assertRaises(ValueError):
            training_data = TrainingData.from_weekday_hour_df(pd.DataFrame(),
                                                              abs_start_dt=None, normalize_cols=None)

    def test_call_construcor_directly_with_missing_rel_time_col(self):
        # print test name
        print(self._testMethodName)
        with self.assertRaises(ValueError):
            training_data = TrainingData(pd.concat([T1_DISTRIBUTION, T2_DISTRIBUTION]),
                                         abs_start_dt=None, normalize_cols=None)






if __name__ == '__main__':
    unittest.main()
