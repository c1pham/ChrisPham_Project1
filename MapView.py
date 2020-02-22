import pandas as pd
import ssl
import plotly.express as px


def make_jobs_map(data: pd.DataFrame):
    ssl._create_default_https_context = ssl._create_unverified_context
    us_cities = data

    print(us_cities)
    print(type(us_cities))
    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="title", hover_data=["additional_info"],
                            color_discrete_sequence=["fuchsia"], zoom=2, height=300)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()
