import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import State, Input, Output
import Main
import datetime
import DataController
import MapView

# https://dash.plot.ly/getting-started
# dash reference to start
# https://dash.plot.ly/state
# reference to dash state

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
current_dataset = Main.main()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Job Seeker'),

    html.Div(children='''
        A Map of Developer Jobs around the world From Github API and Stackoverflow RSS feed.
    ''', className='row'),
    html.Div(children=html.H3(
        children="Job Filters"
    ), className='row'),
    html.Div(children=[
        html.Div(
            children=dcc.DatePickerSingle(
                id="date-selector",
                date=datetime.datetime(2017, 6, 10),
            ),
            className='three columns'
        ),
        html.Div(
            dcc.Input(
                id='company-selection',
                placeholder='company name',
                type="text",
                value="",
            ),
            className='three columns'
        ),

        html.Div(
            children=[
                dcc.Input(
                    id='tech-1-selection',
                    placeholder='technology',
                    type="text",
                    value=""
                ),
                "\t",
                dcc.Input(
                    id='tech-2-selection',
                    placeholder='technology',
                    type="text",
                    value="",
                ),
                "\t",
                dcc.Input(
                    id='tech-3-selection',
                    placeholder='technology',
                    type="text",
                    value="",
                ),
                '\t',
                html.Button(
                    "Apply Filters",
                    id="apply-filters-btn"
                )
            ],
            className='six columns'
        )
    ],
        className='row'
    ),
    html.Div(id="error"),
    dcc.Graph(
        id='jobs-map',
        figure=current_dataset
    )
])


@app.callback([Output('jobs-map', 'figure'),
               Output('error', 'children')],
              [Input(component_id="apply-filters-btn", component_property="n_clicks")],
              [State('date-selector', 'date'),
               State('company-selection', 'value'),
               State('tech-1-selection', 'value'),
               State('tech-2-selection', 'value'),
               State('tech-3-selection', 'value')])
def update_map(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech):
    print(n_clicks)
    error_message = ''
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    all_jobs_from_db = DataController.load_jobs_from_db(job_db_cursor)
    selected_jobs = DataController.load_jobs_created_on_or_after_date(job_db_cursor,
                                                                      DataController.parse_date_time(selected_time))

    if selected_jobs is False:
        # figure out how to make empty map
        jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor, all_jobs_from_db)
        error_message = "Error jobs from this time"
        return MapView.make_jobs_map(jobs_data_frame), error_message

    non_remote_jobs = DataController.get_all_non_remote_jobs(selected_jobs)
    print(first_tech + "first tag")
    print(second_tech + "second tag")
    print(third_tech + "third tag")

    if first_tech != '' or second_tech != '' or third_tech != '':
        tech_jobs = DataController.get_jobs_by_technology(non_remote_jobs, [first_tech, second_tech, third_tech])
        if tech_jobs is not False:
            selected_jobs = tech_jobs
        else:
            jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor,
                                                                                           all_jobs_from_db)
            error_message = "Error no jobs with these tags"
            return MapView.make_jobs_map(jobs_data_frame), error_message

    if selected_company != "":
        company_jobs = DataController.get_all_company_jobs(selected_jobs, selected_company)
        if company_jobs is not False:
            selected_jobs = company_jobs
        else:
            jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor,
                                                                                           all_jobs_from_db)
            error_message = "Error no jobs from this company"
            return MapView.make_jobs_map(jobs_data_frame), error_message
    else:
        selected_jobs = all_jobs_from_db

    jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor, selected_jobs)
    return MapView.make_jobs_map(jobs_data_frame), error_message


if __name__ == '__main__':
    app.run_server(debug=True)
