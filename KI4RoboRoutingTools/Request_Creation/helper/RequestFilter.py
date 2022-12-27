from datetime import datetime, timedelta
import pandas as pd
from .TimeHelperFunction import from_car2go_format


def filter_by_datettime(df: pd.DataFrame, from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
    """
    Filters a dataframe by a given datetime range.
    :param df: The dataframe to filter (not in-place)
    :param from_dt: The start datetime
    :param to_dt: The end datetime
    """
    list_to_drop_idx = []
    for idx, item in df.iterrows():
        # Convert to datetime
        dt = from_car2go_format(item["STARTED_LOCAL"])
        if dt < from_dt or dt > to_dt:
            list_to_drop_idx.append(idx)
    return df.drop(index=list_to_drop_idx)
