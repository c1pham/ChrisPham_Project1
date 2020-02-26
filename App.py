import dash
import dash_core_components as dcc
import dash_html_components as html
import Main

# https://dash.plot.ly/getting-started
# dash reference to start

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
current_dataset = Main.main()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Job Seeker'),

    html.Div(children='''
        A Map of Developer Jobs around the world From Github API and Stackoverflow RSS feed.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=current_dataset
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
