import plotly.express as px
import pandas as pd


def plot_coordinates_with_px(df: pd.DataFrame, title: str):
    fig = px.scatter_geo(df, lat='STARTLAT', lon='STARTLONG', hover_name="STARTED_LOCAL")
    fig.update_layout(title=title, title_x=0.5)
    fig.show()

