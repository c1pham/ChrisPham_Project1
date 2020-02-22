import pandas
import ssl
import plotly.express as px

# https://plot.ly/python/mapbox-layers/
# plotly map reference, use some code from their website then customize for my needs


# edit this to adjust zoom depending on filter used
def make_jobs_map(data: pandas.DataFrame):
    ssl._create_default_https_context = ssl._create_unverified_context
    job_data = data
    fig = px.scatter_mapbox(job_data, lat="lat", lon="lon", hover_name="title",
                            hover_data=["tags"],
                            color_discrete_sequence=["fuchsia"], zoom=2, height=400)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 20, "t": 20, "l": 20, "b": 20})
    fig.show()
