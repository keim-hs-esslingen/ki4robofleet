import pandas as pd
from datetime import datetime

class TrainingData:
    # Dataframe columns: REL_TIME_SECONDS, ROW, COL, REQUESTS
    def __init__(self, df: pd.DataFrame, abs_start_dt: datetime = None, normalize_cols: [] = None):
        self.__abs_start_dt = abs_start_dt
        # maybe do some input validation on df, e.g. if all sectors are present per timestamp
        if len(df) == 0:
            raise ValueError("df is empty")
        # check col names of df
        if not 'REL_TIME_SECONDS' in df.columns:
            raise ValueError("df does not contain column REL_TIME_SECONDS. "
                             "Use class method 'from_weekday_and_hour' instead!")
        if not 'ROW' in df.columns:
            raise ValueError("df does not contain column ROW")
        if not 'COL' in df.columns:
            raise ValueError("df does not contain column COL")
        if not 'REQUESTS' in df.columns:
            raise ValueError("df does not contain column REQUESTS")
        # check if all sectors are present per timestamp
        self.__df = df
        if normalize_cols is not None:
            for col in normalize_cols:
                self.__df[col] = self.__df[col] / self.__df[col].max()

    @classmethod
    # Dataframe columns: WEEKDAY, HOUR, ROW, COL, REQUESTS
    def from_weekday_hour_df(cls, df: pd.DataFrame, abs_start_dt: datetime = None, normalize_cols: [] = None):
        df['REL_TIME_SECONDS'] = df.apply(lambda row: (row['WEEKDAY'] * 24 + row['HOUR']) * 3600, axis=1)
        df.drop(columns=['WEEKDAY', 'HOUR'], inplace=True)
        return cls(df, abs_start_dt, normalize_cols)

    def get_record(self, rel_time_seconds: int, interpolated: bool = True):
        record = self.__df.loc[self.__df['REL_TIME_SECONDS'] == rel_time_seconds]
        if len(record) == 0:
            if not interpolated:
                record = self.__df.loc[self.__df['REL_TIME_SECONDS'] == rel_time_seconds]
                if len(record) == 0:
                    # get next higher timestamp
                    all_next_records = self.__df.loc[self.__df['REL_TIME_SECONDS'] > rel_time_seconds].head(1)
                    record = self.__df.loc[self.df['REL_TIME_SECONDS'] == all_next_records['REL_TIME_SECONDS'].values[0]]
                return record
            else:
                # get next lower timestamp record
                all_previous_records = self.__df.loc[self.__df['REL_TIME_SECONDS'] < rel_time_seconds]
                # get all records with the highest timestamp of all previous records
                previous_records = self.__df.loc[self.__df['REL_TIME_SECONDS'] == all_previous_records['REL_TIME_SECONDS'].max()]
                # get next higher timestamp record
                all_next_records = self.__df.loc[self.__df['REL_TIME_SECONDS'] > rel_time_seconds]
                # get all records with the lowest timestamp of all next records
                next_records = self.__df.loc[self.__df['REL_TIME_SECONDS'] == all_next_records['REL_TIME_SECONDS'].min()]
                if len(previous_records) == 0:
                    print(f"WARNING: No previous record found for rel_time_seconds={rel_time_seconds}"
                          f", taking time '{next_records['REL_TIME_SECONDS'].values[0]}' instead")
                    record = next_records.copy()
                elif len(next_records) == 0:
                    print(f"WARNING: No next record found for rel_time_seconds={rel_time_seconds}"
                          f", taking time '{previous_records['REL_TIME_SECONDS'].values[0]}' instead")
                    record = previous_records.copy()
                else:
                    # interpolate REQUESTS of prev_record and next_record depending on the distance to rel_time_seconds
                    record = previous_records.copy()
                    diff = next_records['REL_TIME_SECONDS'].values[0] - previous_records['REL_TIME_SECONDS'].values[0]
                    part = (rel_time_seconds - previous_records['REL_TIME_SECONDS'].values[0]) / diff
                    record['REQUESTS'] = previous_records['REQUESTS'] + (next_records['REQUESTS'] - previous_records['REQUESTS']) * part
                record['REL_TIME_SECONDS'] = int(rel_time_seconds)
        return record
