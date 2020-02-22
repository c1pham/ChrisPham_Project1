import pandas
import ssl
import plotly.express as px

# https://plot.ly/python/mapbox-layers/
# plotly map reference, use some code from their website


def make_jobs_map(data: pandas.DataFrame):
    ssl._create_default_https_context = ssl._create_unverified_context
    job_data = data
    fig = px.scatter_mapbox(job_data, lat="lat", lon="lon", hover_name="title",
                            hover_data=["additional_info"],
                            color_discrete_sequence=["fuchsia"], zoom=2, height=300)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()
