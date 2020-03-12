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
# will contain all the remote jobs in dash objects
remote_information = None

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# this function collects the jobs, sets up needed databases and saves it onto data
# also makes a map that will show up when the app runs.
# This same map is also used when user puts in a filter that get no jobs
# Lastly this func formats remote jobs data for dash
def prepare_dash_with_data():
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


# this is suppose to merge the two list and does not allow duplicate jobs
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


# this is the app layout that will be used when the program runs
# dcc inputs are input boxes
app.layout = html.Div(children=[
    html.H1(children='Hello Job Seeker'),

    html.Div(children='A Map of Developer Jobs around the world From Github API and Stackoverflow RSS feed',
             className='row'),
    html.Div(children=html.H3(
        children="Job Filters"
    ), className='row'),
    html.Div(children=[
        html.Div(  # this is an object that allows users to select a date form a calendar
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
            html.Div(children=[dcc.Input(
                id="location-filter",
                placeholder="Location",
                type="text",
                value=""
            ), '\t',
                dcc.Input(
                id='miles',
                placeholder='miles away',
                type='number',
                value=''
            )],
                className="six columns"
            ),
            html.Div(children=[
                html.Button(
                    "Apply Filters",
                    id="apply-filters-btn"
                ),
                html.Button(
                    'Get Remote Jobs',
                    id="remote-jobs-btn"
                )],
                className='six columns'
            )
        ])
    ],
        className='row',
        style={'margin-top': "20px",
               'margin-bottom': "10px"}
    ),
    html.Div(id="error"),
    dcc.Graph(  # this holds our jobs map even though it says graph.
        id='jobs-map',
        figure=figure_with_all_non_remote_jobs_on_map
    ),
    html.Div(children=[
        # these items have overflow scroll, so the data doesn't make a long webpage.
        # Instead it is a box that users can scroll down on
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
# states are the current information from this object
@app.callback([Output('jobs-map', 'figure'),
               Output('error', 'children')],
              [Input(component_id="apply-filters-btn", component_property="n_clicks")],
              [State('date-selector', 'date'),
               State('company-selection', 'value'),
               State('tech-1-selection', 'value'),
               State('tech-2-selection', 'value'),
               State('tech-3-selection', 'value'),
               State('job-title', 'value'),
               State('location-filter', 'value'),
               State('miles', 'value')])
def update_map(n_clicks, time, company, first_tech, second_tech, third_tech, job_title, location, miles):
    # when dash runs, this events gets called before we can press anything so that is why if statement is here
    # so if we haven't clicked yet we won't apply all these filters
    if n_clicks is not None:
        return update_map_with_filters(time, company, first_tech, second_tech, third_tech, job_title, location, miles)
    else:
        return figure_with_all_non_remote_jobs_on_map, ''


# this function is what gets called by update_map but can be used with any data
def update_map_with_filters(time, selected_company, first_tech, second_tech, third_tech, job_title, location, miles):
    error_message = 'ERROR: no jobs with these criteria'
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("jobs_cache_db")
    # we want a fresh table in job cache every time because it is this table we use to hold the current job info
    # and will use when we try to select job information from the map
    job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE")
    DataController.create_job_cache_table(job_cache_db_cursor)
    # if company is not in db then no need to continue with filters
    if DataController.is_company_in_db(job_db_cursor, selected_company) is False:
        return figure_with_all_non_remote_jobs_on_map, error_message
    # gets job on or after a certain date
    selected_jobs_after_time = filter_jobs_with_time(job_db_cursor, time)
    if selected_jobs_after_time is False:  # it returns false if no jobs were found
        return figure_with_all_non_remote_jobs_on_map, error_message
    non_remote_jobs = DataController.get_all_non_remote_jobs(selected_jobs_after_time)
    if len(non_remote_jobs) == 0:
        return figure_with_all_non_remote_jobs_on_map, error_message
    selected_jobs = filter_jobs_with_technology(non_remote_jobs, first_tech, second_tech, third_tech)
    if selected_jobs is False:
        return figure_with_all_non_remote_jobs_on_map, error_message
    selected_jobs = filter_jobs_with_company(selected_jobs, selected_company)
    if selected_jobs is False:
        return figure_with_all_non_remote_jobs_on_map, error_message
    selected_jobs = filter_jobs_with_title(selected_jobs, job_title)
    # if any of these conditions are true no need to generate a new data frame and map just return default map
    if selected_jobs is False or len(selected_jobs) == 0:
        return figure_with_all_non_remote_jobs_on_map, error_message

    selected_jobs = filter_jobs_with_location(location, loc_db_cursor, selected_jobs, miles)
    if selected_jobs is False:
        return figure_with_all_non_remote_jobs_on_map, error_message \
               + " DISCLAIMER: NON MAJOR TOWNS OR CITIES MAY NOT BE FOUND BY PROGRAM"
    jobs_data = DataController.process_job_data_into_data_frame(loc_db_cursor, selected_jobs, [job_cache_db_cursor])
    # first object is data frame next object is remote jobs that could not be process by previous func
    jobs_data_frame = jobs_data[0]
    DataController.close_dbs([job_db_connection, loc_db_connection, job_cache_db_connection])
    return MapView.make_jobs_map(jobs_data_frame), "Successful"


# call this function when plot on job map gets clicked
# it will get the jobs with the lat long matching the plot the user pressed
@app.callback(Output('selected-job-info', 'children'),
              [Input('jobs-map', 'clickData')])
def get_job_data_from_graph_click(click_data):
    # this function is called when dash is first run even before we can click so if statement is here to prevent update
    if click_data is not None:
        lat = str(click_data['points'][0]['lat'])
        lon = str(click_data['points'][0]['lon'])
        return DataController.get_selected_jobs_with_lat_long(lat, lon, "jobs_cache_db", "default_jobs_cache_db")
    else:
        raise PreventUpdate


# this will call when remote jobs btn is pressed and will return dash objects containing remote jobs information
@app.callback(Output('remote-job-info', 'children'),
              [Input(component_id="remote-jobs-btn", component_property="n_clicks")])
def update_remote_info(n_clicks):
    # the if statement is here because this function is called before it can be pressed
    # therefore if click data is none no update
    if n_clicks is None:
        raise PreventUpdate
    else:
        return remote_information


# filters out jobs by title
def filter_jobs_with_title(all_jobs, job_title: str):
    stripped_title = job_title.strip()
    if stripped_title != "":  # will filter only if user input is not empty string
        jobs_with_title = DataController.get_all_jobs_with_title(all_jobs, stripped_title)
        if jobs_with_title is not False:
            return jobs_with_title
        else:
            return False
    # if user input is "" then just return all jobs
    return all_jobs


# filters out jobs by company
def filter_jobs_with_company(all_jobs, selected_company: str):
    stripped_company = selected_company.strip()
    if stripped_company != "":  # will filter only if user input is not empty string
        company_jobs = DataController.get_all_company_jobs(all_jobs, stripped_company)
        if company_jobs is not False:  # company jobs is false if no jobs were found
            return company_jobs
        else:
            return False
    # if user input is "" then just returns all jobs
    return all_jobs


# filter out jobs that have one of these technologies, it works as it has first tech or second tech or third tech
def filter_jobs_with_technology(all_jobs: List, first_tech: str, second_tech: str, third_tech: str):
    # if user input is empty then don't filter
    stripped_first_tech = first_tech.strip()
    stripped_second_tech = second_tech.strip()
    stripped_third_tech = third_tech.strip()
    technology = [stripped_first_tech, stripped_second_tech, stripped_third_tech]
    if stripped_first_tech != '' or stripped_second_tech != '' or stripped_third_tech != '':
        tech_jobs = DataController.get_jobs_by_technology(all_jobs, technology)
        if tech_jobs is not False:  # tech jobs return false if no jobs are found
            return tech_jobs
        else:
            return False
    # if user input is "" then just returns all jobs
    return all_jobs


# filter out jobs that happen on or after a specific date
def filter_jobs_with_time(job_db_cursor, selected_time: datetime):
    time = DataController.parse_dash_date(selected_time)
    selected_jobs = DataController.load_jobs_created_on_or_after_date(job_db_cursor, time)
    if selected_jobs is False:  # selected jobs is false if no jobs were found that match the time
        return False
    return selected_jobs


#  filters out jobs base on lat long
def filter_jobs_with_location(location: str, location_cursor, all_jobs: List, miles):
    filtered_jobs = []
    print(location)
    # checks to see if user input is empty
    if location.strip() == "":
        return all_jobs
    all_locations = DataController.load_location_cache(location_cursor)
    location_data = DataController.get_one_place_from_address(location, all_locations, "NOT PROVIDED")
    if location_data is False:
        return False
    location_lat = float(location_data[1])
    location_lon = float(location_data[2])
    # goes through jobs and check if they are within x amount of miles of the requested location
    for job in all_jobs:
        job_location = job['location']
        if DataController.is_job_within_x_miles(job_location, location_lat, location_lon, all_locations, miles):
            filtered_jobs.append(job)
    if len(filtered_jobs) == 0:
        return False
    return filtered_jobs


if __name__ == '__main__':
    default_figure, default_remote_jobs = prepare_dash_with_data()
    figure_with_all_non_remote_jobs_on_map = default_figure
    remote_information = default_remote_jobs
    app.run_server(debug=True)
