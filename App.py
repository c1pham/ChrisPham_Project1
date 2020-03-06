from typing import List
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import State, Input, Output
from dash.exceptions import PreventUpdate
import JobCollector
import datetime
import DataController
import MapView

# https://dash.plot.ly/getting-started
# dash reference to start
# https://dash.plot.ly/state
# reference to dash state
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
figure_with_all_non_remote_jobs_on_map = None
remote_information = None

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def prepare_dash_with_default_job_figure():
    # open db connections
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("jobs_cache_db")
    default_job_cache_db_connection, default_job_cache_db_cursor = DataController.open_db("default_jobs_cache_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE;")
    default_job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE;")

    DataController.create_job_cache_table(job_cache_db_cursor)
    DataController.create_job_cache_table(default_job_cache_db_cursor)
    DataController.create_jobs_table(job_db_cursor)
    DataController.create_location_cache_table(loc_db_cursor)

    github_jobs = JobCollector.get_github_jobs()
    print(len(github_jobs))
    stack_overflow_jobs = JobCollector.get_stack_overflow_jobs()
    # take job info and make it into dictionary the program can use
    processed_github_jobs = DataController.process_all_github_jobs(github_jobs)
    processed_stack_overflow_jobs = DataController.process_all_stack_overflow_jobs(stack_overflow_jobs)
    all_jobs = processed_github_jobs + processed_stack_overflow_jobs
    DataController.save_jobs_to_db(job_db_cursor, all_jobs)
    # save the jobs by committing to db
    DataController.close_db(job_db_connection)
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    # get all jobs from db
    jobs_from_db = DataController.load_jobs_from_db(job_db_cursor)
    non_remote_jobs = DataController.get_all_non_remote_jobs(jobs_from_db)
    jobs_data_frame, remote_or_unknown_jobs = DataController.process_job_data_into_data_frame(
        loc_db_cursor, non_remote_jobs, [job_cache_db_cursor, default_job_cache_db_cursor])
    figure = MapView.make_jobs_map(jobs_data_frame)
    remote_jobs = DataController.get_all_remote_jobs(all_jobs)
    # save jobs and location cache by committing to db
    connections = [job_cache_db_connection, job_db_connection, default_job_cache_db_connection, loc_db_connection]
    DataController.close_dbs(connections)
    return figure, DataController.format_text_from_selected_jobs_into_dash(remote_jobs, "Remote or Unknown Jobs")


def merge_remote_list(all_remote_jobs: List, unknown_or_remote_jobs: List) -> List:
    unique_remote_jobs = all_remote_jobs
    duplicate = False
    for unknown_or_remote_job in unknown_or_remote_jobs:
        for remote_job in all_remote_jobs:
            if remote_job == unknown_or_remote_job:
                duplicate = True
        if duplicate is False:
            unique_remote_jobs.append(unknown_or_remote_job)
    return unique_remote_jobs


app.layout = html.Div(children=[
    html.H1(children='Hello Job Seeker'),

    html.Div(children='A Map of Developer Jobs around the world From Github API and Stackoverflow RSS feed',
             className='row'),
    html.Div(children=html.H3(
        children="Job Filters"
    ), className='row'),
    html.Div(children=[
        html.Div(
            children=dcc.DatePickerSingle(
                id="date-selector",
                date=datetime.datetime(2018, 6, 10),
            ),
            className='two columns'
        ),
        html.Div(
            dcc.Input(
                id='company-selection',
                placeholder='company name',
                type="text",
                value="",
            ),
            className='two columns'
        ),
        html.Div(
            dcc.Input(
                id='job-title',
                placeholder='job title',
                type="text",
                value=""),
            className='two columns'
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
                    value=""
                )
            ],
            className='six columns'
        )
    ], className='row'),
    html.Div(children=[
        html.Div(children=[
            html.Button(
                "Apply Filters",
                id="apply-filters-btn"
            ),
            html.Button(
                'Get Remote Jobs',
                id="remote-jobs-btn"
            )
        ])
    ],
        className='row',
        style={'margin-top': "20px",
               'margin-bottom': "10px"}
    ),
    html.Div(id="error"),
    dcc.Graph(
        id='jobs-map',
        figure=figure_with_all_non_remote_jobs_on_map
    ),
    html.Div(children=[
        # see where textarea should go
        html.Div(
            id="remote-job-info",
            children=remote_information,
            className='six columns',
            style={
                'max-height': '800px',
                'overflow': 'scroll'
            }
        ),
        html.Div(
            id="selected-job-info",
            className='six columns',
            style={
                'max-height': '800px',
                'overflow': 'scroll'
            }
        )
    ], className='row'
    )
])


# when user press button then make update map figure with filters from GUI
@app.callback([Output('jobs-map', 'figure'),
               Output('error', 'children')],
              [Input(component_id="apply-filters-btn", component_property="n_clicks")],
              [State('date-selector', 'date'),
               State('company-selection', 'value'),
               State('tech-1-selection', 'value'),
               State('tech-2-selection', 'value'),
               State('tech-3-selection', 'value'),
               State('job-title', 'value')])
def update_map(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech, job_title):
    if n_clicks is not None:
        return update_map_with_filters(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech,
                                       job_title)
    else:
        return figure_with_all_non_remote_jobs_on_map, ''


# this function is what gets called by update_map but can be used with any data
def update_map_with_filters(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech, job_title):
    error_message = 'ERROR: no jobs with these criteria'
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("jobs_cache_db")

    if n_clicks is not None:
        job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE")
        DataController.create_job_cache_table(job_cache_db_cursor)

    if DataController.is_company_in_db(job_db_cursor, selected_company) is False:
        return figure_with_all_non_remote_jobs_on_map, error_message

    selected_jobs_after_time = filter_jobs_with_time(job_db_cursor, selected_time)
    if selected_jobs_after_time is False:
        return figure_with_all_non_remote_jobs_on_map, error_message
    non_remote_jobs = DataController.get_all_non_remote_jobs(selected_jobs_after_time)
    selected_jobs = filter_jobs_with_technology(non_remote_jobs, first_tech, second_tech, third_tech)
    selected_jobs = filter_jobs_with_company(selected_jobs, selected_company)
    selected_jobs = filter_jobs_with_title(selected_jobs, job_title)

    if selected_jobs is False or len(selected_jobs) == 0:
        return figure_with_all_non_remote_jobs_on_map, error_message

    jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor, selected_jobs,
                                                                                   [job_cache_db_cursor])
    DataController.close_dbs([job_db_connection, loc_db_connection, job_cache_db_connection])
    return MapView.make_jobs_map(jobs_data_frame), "Successful"


@app.callback(Output('selected-job-info', 'children'),
              [Input('jobs-map', 'clickData')])
def get_job_data_from_graph_click(click_data):
    if click_data is not None:
        lat = str(click_data['points'][0]['lat'])
        lon = str(click_data['points'][0]['lon'])
        return DataController.get_selected_jobs_with_lat_long(lat, lon, "jobs_cache_db", "default_jobs_cache_db")
    else:
        raise PreventUpdate


@app.callback(Output('remote-job-info', 'children'),
              [Input(component_id="remote-jobs-btn", component_property="n_clicks")])
def update_remote_info(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        return remote_information


def filter_jobs_with_title(all_jobs, job_title):
    if job_title != "":
        jobs_with_title = DataController.get_all_jobs_with_title(all_jobs, job_title)
        if jobs_with_title is not False:
            return jobs_with_title
        else:
            return False
    return all_jobs


def filter_jobs_with_company(all_jobs, selected_company):
    if selected_company != "":
        company_jobs = DataController.get_all_company_jobs(all_jobs, selected_company)
        if company_jobs is not False:
            return company_jobs
        else:
            return False
    return all_jobs


def filter_jobs_with_technology(all_jobs, first_tech, second_tech, third_tech):
    if first_tech != '' or second_tech != '' or third_tech != '':
        tech_jobs = DataController.get_jobs_by_technology(all_jobs, [first_tech, second_tech, third_tech])
        if tech_jobs is not False:
            return tech_jobs
        else:
            return False
    return all_jobs


def filter_jobs_with_time(job_db_cursor, selected_time: datetime):
    time = DataController.parse_date_time(selected_time)
    selected_jobs = DataController.load_jobs_created_on_or_after_date(job_db_cursor, time)
    if selected_jobs is False:
        return False
    return selected_jobs


if __name__ == '__main__':
    default_figure, default_remote_jobs = prepare_dash_with_default_job_figure()
    figure_with_all_non_remote_jobs_on_map = default_figure
    remote_information = default_remote_jobs
    app.run_server(debug=True)
