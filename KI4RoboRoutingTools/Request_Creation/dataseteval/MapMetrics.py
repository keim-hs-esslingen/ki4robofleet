import pandas as pd
import requests
import geopy.distance
from datetime import datetime

def process_map_metrics(df: pd.DataFrame):
    metrics = {}
    #print(f"Maximum value {df.max()}")
    #print(f"Minimum value {df.min()}")
    metrics['rowcount'] = df.shape[0]
    metrics['featurecount'] = df.shape[1]
    print(f"Rows (dataset count): {metrics['rowcount']}, Columns (features): {metrics['featurecount']}")
    metrics['minlat'] = df['STARTLAT'].min()
    metrics['maxlat'] = df['STARTLAT'].max()
    metrics['minlong'] = df['STARTLONG'].min()
    metrics['maxlong'] = df['STARTLONG'].max()
    print(f"MIN LAT : {metrics['minlat']}, MAX LAT : {metrics['maxlat']}")
    print(f"MIN LONG: {metrics['minlong']}, MAX LONG: {metrics['maxlong']}")
    metrics['mintime'] = df['STARTED_LOCAL'].min()
    metrics['maxtime'] = df['STARTED_LOCAL'].max()
    print(f"Time from {metrics['mintime']} to {metrics['maxtime']}")
    coord_north = (df['STARTLAT'].max(), df['STARTLONG'].min())
    coord_south = (df['STARTLAT'].min(), df['STARTLONG'].min())
    coord_east = (df['STARTLAT'].max(), df['STARTLONG'].min())
    coord_west = (df['STARTLAT'].max(), df['STARTLONG'].max())

    metrics['distance_northsouth'] = geopy.distance.geodesic(coord_north, coord_south).km
    print(f"Distance North - South: {metrics['distance_northsouth']:.2f} km")
    metrics['distance_eastwest'] = geopy.distance.geodesic(coord_east, coord_west).km
    print(f"Distance East  - West : {metrics['distance_eastwest']:.2f} km")
    metrics['avgtriplength'] = df['DISTANCE'].mean()
    print(f"Average trip length: {metrics['avgtriplength']:.2f} miles/km?")
    metrics['avgtripduration'] = df['DURATION'].mean()
    print(f"Average trip duration: {metrics['avgtripduration']:.2f} s / {metrics['avgtripduration']/60:.2f} min")
    try:
        lat_center_ns = (metrics['maxlat'] + metrics['minlat'])/2.
        long_center = (metrics['maxlong'] + metrics['minlong']) / 2.
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat_center_ns}&lon={long_center}&format=json")
        address = res.json()['address']
        metrics['city'] = address['city']
        metrics['county'] = address['county']
        metrics['state'] = address['state']
        metrics['zipcode'] = address['postcode']
        metrics['country'] = address['country']
    except:
        pass

    timediff = pd.to_timedelta(pd.to_datetime(metrics['maxtime']) - pd.to_datetime(metrics['mintime']), unit='hours')
    timediff_hours = timediff.days * 24 + timediff.seconds / 3600
    area = metrics['distance_northsouth'] * metrics['distance_eastwest']
    #datetime_max = datetime.strptime(metrics['maxtime'], '%y-%m-%d %H:%M:%S')
    metrics['avgRequestsPerKilometerPerHour'] = metrics['rowcount']/ area / timediff_hours
    print(f"Average requests per kilometer per hour: {metrics['avgRequestsPerKilometerPerHour']:.3f}")

    return metrics


#import geopandas
#import contextily as cx

#def plot_coordinates_with_geopandas(df: pd.DataFrame):
