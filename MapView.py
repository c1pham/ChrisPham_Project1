import pandas
import ssl
import plotly.express as px

# https://plot.ly/python/mapbox-layers/
# plotly map reference, use some code from their website then customize for my needs


# edit this to adjust zoom depending on filter used
def make_jobs_map(data: pandas.DataFrame):
    # monkey patch
    ssl._create_default_https_context = ssl._create_unverified_context
    job_data = data
    # create map
    fig = px.scatter_mapbox(job_data, lat="lat", lon="lon", hover_name="jobs_info",
                            color_discrete_sequence=["fuchsia"], zoom=2, height=500)
    fig.update_layout(mapbox_style="open-street-map")  # free mapbox style to use without token
    fig.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 20})
    return fig


def make_centered_jobs_map(data: pandas.DataFrame, lat: float, lon: float):
    # monkey patch
    ssl._create_default_https_context = ssl._create_unverified_context
    job_data = data
    # create map
    fig = px.scatter_mapbox(job_data, lat="lat", lon="lon", hover_name="jobs_info",
                            color_discrete_sequence=["fuchsia"], zoom=4, height=500, center=dict(lat=lat, lon=lon))
    fig.update_layout(mapbox_style="open-street-map")  # free mapbox style to use without token
    fig.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 20})
    return fig
