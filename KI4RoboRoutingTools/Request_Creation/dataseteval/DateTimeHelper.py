import pandas as pd

def enrich_weekday_and_hour_legacy(df: pd.DataFrame): # adds WEEKDAY and HOUR
    dt_series = pd.to_datetime(df["STARTED_LOCAL"])
    dt_df_weekday = pd.DataFrame({'WEEKDAY': []}, dtype="int32")
    dt_df_hour = pd.DataFrame({'HOUR': []}, dtype="int32")
    for idx, dt_datetime in dt_series.iteritems():
        # dt_series_weekday = dt_series_weekday.append({'WEEKDAY':dt_datetime.weekday()}, ignore_index=True)
        temp_df_weekday = pd.DataFrame(data=[dt_datetime.weekday()], index=[idx], columns=['WEEKDAY'], dtype="int32")
        temp_df_hour = pd.DataFrame(data=[dt_datetime.hour], index=[idx], columns=['HOUR'], dtype="int32")
        dt_df_weekday = pd.concat([dt_df_weekday, temp_df_weekday])
        dt_df_hour = pd.concat([dt_df_hour, temp_df_hour])
    ret_df = df.join(dt_df_weekday)
    ret_df = ret_df.join(dt_df_hour)
    return ret_df

def enrich_weekday_and_hour(df: pd.DataFrame): # adds WEEKDAY and HOUR
    dt_series = pd.to_datetime(df["STARTED_LOCAL"])
    df["HOUR"] = dt_series.dt.hour
    df["WEEKDAY"] = dt_series.dt.weekday

