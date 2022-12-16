import plotly.express as px
import pandas as pd


def plot_coordinates_with_px(df: pd.DataFrame, title: str):
    fig = px.scatter_geo(df, lat='STARTLAT', lon='STARTLONG', hover_name="STARTED_LOCAL")
    fig.update_layout(title=title, title_x=0.5)
    fig.show()


import folium

def plot_folium(df: pd.DataFrame):
    m = folium.Map(location=[40.70, -73.94], zoom_start=10, tiles='CartoDB positron')
    for _, r in df.iterrows():
        # without simplifying the representation of each borough, the map might not be displayed
        sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, )
        folium.Popup(r['BoroName']).add_to(geo_j)
        geo_j.add_to(m)
#import geopandas
#import contextily as cx

#def plot_coordinates_with_geopandas(df: pd.DataFrame):
