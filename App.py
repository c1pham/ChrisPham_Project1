from typing import List
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import State, Input, Output
import JobCollector
import datetime
import DataController
import MapView

# https://dash.plot.ly/getting-started
# dash reference to start
# https://dash.plot.ly/state
# reference to dash state


def prepare_dash_with_default_job_figure():
    # open db connections
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("jobs_cache_db")
    job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE;")
    DataController.create_job_cache_table(job_cache_db_cursor)
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    # create tables
    DataController.create_jobs_table(job_db_cursor)
    DataController.create_location_cache_table(loc_db_cursor)

    github_jobs = JobCollector.get_github_jobs()
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
        loc_db_cursor, non_remote_jobs, job_cache_db_cursor)
    figure = MapView.make_jobs_map(jobs_data_frame)
    remote_jobs = DataController.get_all_remote_jobs(all_jobs)
    # save jobs and location cache by committing to db
    DataController.close_db(job_db_connection)
    DataController.close_db(loc_db_connection)
    DataController.close_db(job_cache_db_connection)
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


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
figure_with_all_non_remote_jobs_on_map, remote_information = prepare_dash_with_default_job_figure()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

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
            className='eight columns'
        )
    ],
        className='row'
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
                'max-height': '500px',
                'overflow': 'scroll'
            }
        ),
        html.Div(
            id="selected-job-info",
            className='six columns',
            style={
                'max-height': '500px',
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
               State('tech-3-selection', 'value')])
def update_map(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech):
    return update_map_with_filters(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech)


# this function is what gets called by update_map but can be used with any data
def update_map_with_filters(n_clicks, selected_time, selected_company, first_tech, second_tech, third_tech):
    error_message = 'ERROR: no jobs with these criteria'
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("jobs_cache_db")

    if n_clicks is not None:
        job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE")
        DataController.create_job_cache_table(job_cache_db_cursor)

    if DataController.is_company_in_db(job_db_cursor, selected_company) is False:
        return figure_with_all_non_remote_jobs_on_map, error_message

    selected_jobs = DataController.load_jobs_created_on_or_after_date(job_db_cursor,
                                                                      DataController.parse_date_time(selected_time))
    if selected_jobs is False:
        # figure out how to make empty map
        return figure_with_all_non_remote_jobs_on_map, error_message
    non_remote_jobs = DataController.get_all_non_remote_jobs(selected_jobs)
    # this filters job for technology if at least one of the technologies has user input in it
    if first_tech != '' or second_tech != '' or third_tech != '':
        tech_jobs = DataController.get_jobs_by_technology(non_remote_jobs, [first_tech, second_tech, third_tech])
        if tech_jobs is not False:
            selected_jobs = tech_jobs
        else:
            return figure_with_all_non_remote_jobs_on_map, error_message

    if selected_company != "":
        company_jobs = DataController.get_all_company_jobs(selected_jobs, selected_company)
        if company_jobs is not False:
            selected_jobs = company_jobs
        else:
            return figure_with_all_non_remote_jobs_on_map, error_message

    jobs_data_frame, remote_jobs = DataController.process_job_data_into_data_frame(loc_db_cursor, selected_jobs,
                                                                                   job_cache_db_cursor)
    DataController.close_db(job_cache_db_connection)
    DataController.close_db(loc_db_connection)
    DataController.close_db(job_db_connection)
    error_message = "Successful"
    return MapView.make_jobs_map(jobs_data_frame), error_message


@app.callback(Output('selected-job-info', 'children'),
              [Input('jobs-map', 'clickData')])
def get_job_data_from_graph_click(click_data):
    if click_data is not None:
        lat = str(click_data['points'][0]['lat'])
        lon = str(click_data['points'][0]['lon'])
        jobs_cache_connection, jobs_cache_cursor = DataController.open_db('jobs_cache_db')
        job_cache = DataController.load_jobs_cache(jobs_cache_cursor)
        jobs_with_lat_lon = DataController.get_jobs_from_cache_with_lat_long(job_cache, lat, lon)
        formatted_text = DataController.format_text_from_selected_jobs_into_dash(jobs_with_lat_lon, "Selected Map Jobs")
        DataController.close_db(jobs_cache_connection)
        return formatted_text
    return None


if __name__ == '__main__':
    app.run_server(debug=True)
