import pandas as pd


def convert_nyc_to_sumo4av_format(file_path) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    # reading and formatting Pickup- Date and Time
    # this is a bit tricky, because you havee to type %I
    df['STARTED_LOCAL'] = pd.to_datetime(df['lpep_pickup_datetime'], format="%m/%d/%Y %I:%M:%S %p")\
        .dt.strftime("%Y-%m-%d %H:%M:%S")

    df['STARTLAT'] = df['Pickup_latitude']
    df['STARTLONG'] = df['Pickup_longitude']
    df['FINISHLAT'] = df['Dropoff_latitude']
    df['FINISHLONG'] = df['Dropoff_longitude']

    df = df.drop(columns=df.columns.difference(['STARTED_LOCAL', 'STARTLAT', 'STARTLONG', 'FINISHLAT', 'FINISHLONG']))

    return df

def filter_by_lat_long(df, long_min, lat_min, long_max, lat_max):
    df = df[
        (df['STARTLAT'] > lat_min) & (df['STARTLAT'] < lat_max)
        & (df['FINISHLAT'] > lat_min) & (df['FINISHLAT'] < lat_max)
        & (df['STARTLONG'] > long_min) & (df['STARTLONG'] < long_max)
        & (df['FINISHLONG'] > long_min) & (df['FINISHLONG'] < long_max)
    ]
    return df
