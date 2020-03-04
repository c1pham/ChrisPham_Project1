from urllib.error import HTTPError
import pandas
from typing import List
from typing import Dict
from typing import Tuple
import sqlite3
import geopy
from geotext import GeoText
import numpy
from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut
import re
import dash_html_components as html
from bs4 import BeautifulSoup

# https://www.btelligent.com/en/blog/best-practice-for-sql-statements-in-python/
# reference for parametrised queries
# https://pypi.org/project/geopy/
# reference for geopy documentation
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
# reference to learn pandas, code is not copied but just used for referenced
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# reference to remove html tags
# format text to fit plotly hover text, however this may be used for text formatting later on GUI


def remove_html_tags_from_text(html_text: str):
    soup = BeautifulSoup(html_text, 'html.parser')
    text_without_html = soup.get_text()
    return text_without_html


def format_text_to_fit_hover_text(text: str):
    text_without_html = remove_html_tags_from_text(text)
    words = text_without_html.split(" ")
    formatted_text = ""
    current_line_size = 0
    for word in words:  # add words to formatted text
        if current_line_size > 80:  # add line break if line is too long
            formatted_text += "<br>"
            current_line_size = 0
        formatted_text += word + " "
        current_line_size += len(word)
    return formatted_text


# create data frame for plotly to plot on map, has 4 columns, title, latitude, longitude, additional info
def process_job_data_into_data_frame(job_cursor: sqlite3.Cursor, job_data: List, job_cache_cursors: List):
    all_jobs = []
    locations_tried = load_location_cache(job_cursor)  # previous locations checked before
    columns = ['jobs_info', 'lat', 'lon']  # columns for data frame
    remote_or_unknown_locations = []
    job_cache = []

    for job_posting in job_data:
        location = job_posting['location']
        title_info = job_posting['title'] + " Tags: " + job_posting['additional_info']
        # keeps if location has already been requested
        if location in locations_tried:
            # grab location then make array for numpy array and add to all all jobs
            cache_coordinates = locations_tried[location]
            current_job_data = [title_info, cache_coordinates[0], cache_coordinates[1]]
            all_jobs.append(current_job_data)
            job_cache_data = {'title': job_posting['title'], 'description': job_posting['description'],
                              'company': job_posting['company'], 'lat': cache_coordinates[0],
                              'lon': cache_coordinates[1]}
            job_cache.append(job_cache_data)
        else:
            location_data = get_lat_long_coordinates_from_address(location)
            if location_data is None:
                # if we can't get address from current string try to get cities with geo text then add
                plotly_data = get_one_place_from_address(location, locations_tried, title_info)
                if plotly_data is not False:
                    job_cache_data = {'title': job_posting['title'], 'description': job_posting['description'],
                                      'company': job_posting['company'], 'lat': plotly_data[1],
                                      'lon': plotly_data[2]}
                    job_cache.append(job_cache_data)
                    all_jobs.append(plotly_data)
                if plotly_data is False:
                    remote_or_unknown_locations.append(job_posting)
            elif location_data is not False:
                job_cache_data = {'title': job_posting['title'], 'description': job_posting['description'],
                                  'company': job_posting['company'], 'lat': location_data[1],
                                  'lon': location_data[2]}
                job_cache.append(job_cache_data)
                # if we got something from class function to find coordinates then add to list
                locations_tried[location_data[0]] = (location_data[1], location_data[2])
                current_job_data = [title_info, location_data[1], location_data[2]]
                all_jobs.append(current_job_data)

    add_all_locations_to_db(job_cursor, locations_tried)  # put new locations into db
    for cursor in job_cache_cursors:
        add_to_jobs_cache(cursor, job_cache)
    all_jobs_no_repeats = process_job_data_into_single_shared_map_box_points(all_jobs)

    numpy_array = numpy.array(all_jobs_no_repeats)
    data_frame = pandas.DataFrame(numpy_array, columns=columns)
    # lat and lon are floats because they will be use for coordinates
    data_frame['lat'] = data_frame['lat'].astype(float)
    data_frame['lon'] = data_frame['lon'].astype(float)
    return data_frame, remote_or_unknown_locations


# takes in a list or list that have order of objects job info, lat, lon
# returns a list or list with all the job info with the same coordinates being in the same string
def process_job_data_into_single_shared_map_box_points(all_jobs: List):
    coordinates_used_for_jobs_for_mapbox = {}
    # combine places with duplicate latitude and longitude coordinates and combine them into 1 entry
    for job_posting in all_jobs:
        key = str(job_posting[1]) + " " + str(job_posting[2])
        if key in coordinates_used_for_jobs_for_mapbox:
            coordinates_used_for_jobs_for_mapbox[key] += "<br>" + job_posting[0]
        else:
            coordinates_used_for_jobs_for_mapbox[key] = job_posting[0]
    all_jobs_no_repeats = []
    for key in coordinates_used_for_jobs_for_mapbox:
        coordinates = key.split(" ")
        latitude = coordinates[0]
        longitude = coordinates[1]
        info = coordinates_used_for_jobs_for_mapbox[key]
        plotly_data_point = [info, latitude, longitude]
        all_jobs_no_repeats.append(plotly_data_point)
    return all_jobs_no_repeats


# takes all stack overflow data and makes a list of dictionaries to ready data for save to db function
def process_all_stack_overflow_jobs(all_jobs):
    processed_jobs = []
    for job in all_jobs:
        processed_job = process_stack_overflow_job(job)
        if processed_jobs is False:
            continue
        processed_jobs.append(processed_job)
    return processed_jobs


# process data from stack overflow
def process_stack_overflow_job(job_data: Dict):
    processed_job = {}
    job_keys = {'id': ['api_id'], 'type': ['job_type'], 'link': ['url'], 'published': ['created_at'],
                'author': ['company'], 'location': [], 'title': [], 'summary': ['description'], 'company_url': [],
                'how_to_apply': ["how_to_apply_info"], 'company_logo': ['company_logo_url']}
    essential_keys = ['title', 'company', 'published']
    # if it missing needed keys then drop the data
    if is_invalid_job_data(essential_keys, job_data) is True:
        return False
    # if the key is not in the job data add it with None data
    for key in job_keys.keys():
        if key not in job_data.keys():
            job_data[key] = None

    # process the job data creating a new data structure with keys that match up with column names
    processed_job = job_data_adaptor(job_keys, job_data, processed_job)

    # will add the tag information to additional info
    if "tags" not in job_data.keys():
        processed_job['additional_info'] = "NOT PROVIDED"
    else:
        tags = job_data['tags']
        tags_into_database = ""
        for tag in tags:
            tags_into_database += tag['term'] + ", "
        tags_into_database = tags_into_database.rstrip(", ")
        processed_job['additional_info'] = tags_into_database
    return processed_job


# this function takes in the job data, the jobs keys, and dictionary to hold processed data
# it will make a new dictionary that is appropriate for the dictionary
# for job keys it needs to take a dictionary with the key from the online job data dictionary
# it needs to have an array for the value, if the jobs table has a column name different
# than API data then include in the key's array the column name of the data table
def job_data_adaptor(job_keys, job_data, processed_job):
    for key in job_keys.keys():
        if key in job_data.keys():
            value = job_data[key]
            if value is None:
                # if the value is none then replace it with not provided
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = "NOT PROVIDED"
                else:
                    processed_job[key] = "NOT PROVIDED"
            else:  # check to see if key has value of length 1, that means they had a different column name
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = job_data[key]
                else:  # rest of other keys names match up to column names
                    processed_job[key] = job_data[key]
        else:  # if the key is not in the dictionary will make the add the key pair with the value of it not provided
            value = job_data[job_keys[key][0]]
            if value is not None:
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = value
                else:
                    processed_job[key] = value
            else:
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = "NOT PROVIDED"
                else:
                    processed_job[key] = "NOT PROVIDED"
    return processed_job


# process all jobs, formatting data structure so it so it can be saved to database no problem
def process_all_github_jobs(all_jobs: List[Dict]) -> List[Dict]:
    processed_jobs = []
    for job in all_jobs:
        processed_job = process_github_job(job)
        if processed_jobs is False:
            pass
        processed_jobs.append(processed_job)
    return processed_jobs


# works ad adapter class, moves job data to a new dictionary
def process_github_job(job_data: Dict):
    processed_job = {}
    job_data["additional_info"] = "NOT PROVIDED"
    # keys that would be in dictionary
    job_keys = {'id': ['api_id'], 'type': ['job_type'], 'url': [], 'created_at': [], 'company': [], 'company_url': [],
                'location': [], 'title': [], 'description': [], 'how_to_apply': ["how_to_apply_info"],
                'company_logo': ['company_logo_url'], "additional_info": []}
    essential_keys = ['title', 'company', 'created_at', 'description']

    if is_invalid_job_data(essential_keys, job_data) is True:
        return False

    return job_data_adaptor(job_keys, job_data, processed_job)


# checks the data in the table and if an essential data is None then it will return false
def is_invalid_job_data(essential_key, job_data):
    for key in job_data:
        if job_data[key] is None and key in essential_key:
            return True


# iterates through and save jobs
def save_jobs_to_db(db_cursor: sqlite3.Cursor, all_jobs: List):
    for entry in all_jobs:  # go through each job posting and then add it to database table
        add_job_to_db(db_cursor, entry)


# make connection to database and return the connection and cursor
def open_db(file_name: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_connection = sqlite3.connect(file_name)
    db_cursor = db_connection.cursor()
    return db_connection, db_cursor


# close database and save data
def close_db(connection: sqlite3.Connection):
    connection.commit()  # save changes to db
    connection.close()


# create table for jobs to be stored
def create_jobs_table(db_cursor: sqlite3.Cursor):
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS jobs(
    job_no INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    job_type TEXT,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    api_id TEXT,
    url TEXT,
    created_at TEXT,
    how_to_apply_info TEXT NOT NULL,
    company_logo_url TEXT,
    company_url TEXT,
    additional_info TEXT
    );''')


# create table to store previous locations
def create_location_cache_table(db_cursor: sqlite3.Cursor):
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS locations_cache(
    location TEXT NOT NULL,
    latitude TEXT NOT NULL,
    longitude TEXT NOT NULL
    );''')


def create_job_cache_table(db_cursor: sqlite3.Cursor):
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS jobs_cache(
    job_no INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    description TEXT NOT NULL,
    latitude TEXT NOT NULL,
    longitude TEXT NOT NULL
    );''')


def add_to_jobs_cache(cursor: sqlite3.Cursor, job_data: List):
    for job in job_data:
        sql_data = (job['title'], job['company'], job['description'], job['lat'], job['lon'])
        sql_statement = 'INSERT INTO JOBS_CACHE (title, company, description, latitude, longitude) VALUES (?,?,?,?,?)'
        cursor.execute(sql_statement, sql_data)


# this function is used to save individual jobs to database
def add_job_to_db(cursor: sqlite3.Cursor, job_data: Dict):
    if job_data is False:
        return
    if is_unique_in_job_table(cursor, job_data) is False:
        return
    #  data to be entered
    sql_data = (job_data['title'], job_data['job_type'], job_data['company'], job_data['location'],
                job_data['description'], job_data['api_id'], job_data['url'], parse_date(job_data['created_at']),
                job_data['how_to_apply_info'], job_data['company_logo_url'], job_data['company_url'],
                job_data['additional_info'])
    # SQL statement to insert data into jobs table
    sql_statement = '''INSERT INTO JOBS (title, job_type, company, location, description, api_id, url, created_at
    , how_to_apply_info, company_logo_url, company_url, additional_info)  VALUES (?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    # insert new entry to table
    cursor.execute(sql_statement, sql_data)


def add_all_locations_to_db(cursor: sqlite3.Cursor, location_data: Dict):
    for key in location_data:
        if is_unique_in_location_table(cursor, key) is False:
            continue
        #  data to be entered
        sql_data = (key, location_data[key][0], location_data[key][1])
        # SQL statement to insert data into jobs table
        sql_statement = 'INSERT INTO LOCATIONS_CACHE (location, latitude, longitude)  VALUES (?, ?, ?);'
        # insert new entry to table
        cursor.execute(sql_statement, sql_data)


def is_unique_in_job_table(cursor: sqlite3.Cursor, job_data: Dict):
    sql_data = (job_data['api_id'],)
    # SQL statement to insert data into jobs table
    sql_statement = 'SELECT * FROM JOBS WHERE api_id = ?;'
    results = cursor.execute(sql_statement, sql_data)
    return len(list(results)) == 0


def is_unique_in_location_table(cursor: sqlite3.Cursor, address: str):
    sql_data = (address,)
    # SQL statement to insert data into jobs table
    sql_statement = 'SELECT * FROM LOCATIONS_CACHE WHERE location = ?;'
    results = cursor.execute(sql_statement, sql_data)
    return len(list(results)) == 0


# go through a string for time and returns a string for time in the month day and year format
def parse_date(date: str) -> str:
    date_dict = {}
    months = ["Jan", "Feb", "Mar", "Apr", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ones_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    tens_digits = ['0', '1', '2', '3']
    date_parts = date.split(" ")

    for time_data in date_parts:
        if time_data in months:
            month = str(months.index(time_data) + 1)  # add one because indexing starts at 0 when months start from 1
            if len(month) == 1:
                month = "0" + month
            date_dict['month'] = month
        elif len(time_data) == 4:  # if length is 4 then it is the year
            date_dict['year'] = time_data
        elif len(time_data) == 2:  # if length is 2 then it most likely the day
            if time_data[0] in tens_digits and time_data[1] in ones_digits:
                date_dict['day'] = time_data
    return date_dict['year'] + "-" + date_dict['month'] + "-" + date_dict['day']


# given a date time, parse the info into YYYY-MM-DD format for db use
def parse_date_time(date: str):
    date_parts = date.split("-")
    year = date_parts[0]
    month = date_parts[1]
    day = date_parts[2][:2]
    return year + "-" + month + "-" + day


def get_lat_long_coordinates_from_address(address: str):
    geo_locator = geopy.geocoders.Nominatim(user_agent="ChrisPham_Project1")
    location = None
    try:
        location = geo_locator.geocode(address, timeout=700)
    except HTTPError:
        print("http error")
        return False
    except GeocoderTimedOut:
        print("geocode timed out")
        return get_lat_long_coordinates_from_address(address)
    except GeocoderQuotaExceeded:
        print("geocode quota exceeded error")
        return False

    # print(location)
    if location is None:
        # print(address + " could not find location")
        return None

    return address, location.latitude, location.longitude, location


def get_one_place_from_address(location: str, locations_tried: Dict, info: str):
    cities = GeoText(location).cities
    for city in cities:
        # only add one of the multiple cities from geotext
        # if in locations tried add it with the coordinates, if not use class function to find coordinates
        if city in locations_tried:
            cache_coordinates = locations_tried[city]
            return [info, cache_coordinates[0], cache_coordinates[1]]
        else:
            location_data = get_lat_long_coordinates_from_address(city)
            if location_data is None:
                continue
            elif location_data is not False:
                locations_tried[location_data[0]] = (location_data[1], location_data[2])
                return [info, location_data[1], location_data[2]]
    # this does the same as the code before but with countries
    return get_one_country_from_address(location, locations_tried, info)


def get_one_country_from_address(location: str, locations_tried: Dict, info: str):
    countries = GeoText(location).countries
    for country in countries:
        if country in locations_tried:
            cache_coordinates = locations_tried[country]
            return [info, cache_coordinates[0], cache_coordinates[1]]
        else:
            location_data = get_lat_long_coordinates_from_address(country)
            if location_data is not False and not None:
                locations_tried[location_data[0]] = (location_data[1], location_data[2])
                return [info, location_data[1], location_data[2]]
    return False


# problem if jobs can count as location and remote then what do we do?
def get_all_remote_jobs(all_jobs: List) -> List:
    all_remote_jobs = []
    for job in all_jobs:
        location = job['location'].lower()
        if location.find('remote') != -1 or location == "not provided":
            all_remote_jobs.append(job)
    return all_remote_jobs


# problem if jobs can count as location and remote then what do we do?
def get_all_non_remote_jobs(all_jobs: List) -> List:
    all_non_remote_jobs = []
    for job in all_jobs:
        location = job['location'].lower()
        if location != "not provided":
            all_non_remote_jobs.append(job)
    return all_non_remote_jobs


def get_all_company_jobs(all_jobs: List, company_name: str):
    all_company_jobs = []
    for job in all_jobs:
        company = job['company'].lower()
        if company == company_name.lower():
            all_company_jobs.append(job)
    if len(all_company_jobs) == 0:
        return False
    return all_company_jobs


# gets job that has at least one of the technologies stored in tags
def get_jobs_by_technology(all_jobs: List, ui_tags: List) -> List:
    all_jobs_with_technology = []
    tags = []
    for tag in ui_tags:
        if tag != "":
            tags.append(tag)

    for job in all_jobs:
        has_technology = False
        for technology in tags:
            if job['additional_info'] != "NOT PROVIDED" and job['additional_info'].find(technology) != -1:
                has_technology = True
            elif job['title'].find(technology) != -1:
                has_technology = True
            elif job['description'].find(technology) != -1:
                has_technology = True
        if has_technology is True:
            all_jobs_with_technology.append(job)

    if len(all_jobs) == 0:
        return False
    return all_jobs_with_technology


# get all location data from db then make return a dictionary with the keys being the location
# and the coordinates in a tuple being the value
def load_location_cache(cursor: sqlite3.Cursor):
    all_locations = {}
    sql_statement = 'SELECT * FROM LOCATIONS_CACHE;'
    results = cursor.execute(sql_statement)
    location_cache = list(results)
    for location in location_cache:
        all_locations[location[0]] = (location[1], location[2])
    return all_locations


# load all jobs from the database
def load_jobs_from_db(cursor: sqlite3.Cursor) -> List:
    all_jobs = []
    sql_statement = 'SELECT * FROM JOBS;'
    results = list(cursor.execute(sql_statement))
    for job in results:
        job_data = process_db_job_data(job)
        all_jobs.append(job_data)
    return all_jobs


def load_jobs_cache(cursor: sqlite3.Cursor):
    all_job_cache = []
    sql_statement = 'SELECT * FROM JOBS_CACHE'
    results = list(cursor.execute(sql_statement))
    for job in results:
        job_cache = process_db_job_cache(job)
        all_job_cache.append(job_cache)
    return all_job_cache


def get_jobs_from_cache_with_lat_long(job_cache: List, lat: str, lon: str):
    jobs_with_lat_lon = []
    for job in job_cache:
        if job['lat'] == lat and job['lon'] == lon:
            jobs_with_lat_lon.append(job)
    return jobs_with_lat_lon


def format_text_from_selected_jobs_into_dash(all_jobs, header: str):
    dash_output = [html.H1(header)]
    count = 0
    for job in all_jobs:
        count += 1
        dash_output.append(html.H6(str(count) + ". Title: " + job['title']))
        dash_output.append(html.Div("Company: " + job['company']))
        dash_output.append(html.Div("Description: " + remove_html_tags_from_text(job['description'])))
    return dash_output


# get jobs in database that is after or on a certain date, format needed is YYYY-MM-DD
def load_jobs_created_on_or_after_date(cursor: sqlite3.Cursor, date: str):
    all_jobs = []
    sql_statement = "SELECT * FROM JOBS WHERE julianday(created_at) >= julianday(?);"
    results = list(cursor.execute(sql_statement, (date,)))
    if len(results) == 0:
        return False
    for job in results:
        job_data = process_db_job_data(job)
        all_jobs.append(job_data)
    return all_jobs


# this is so app.py can reject looking through data if a company does not exist at all
def is_company_in_db(cursor: sqlite3.Cursor, company_name: str):
    results = cursor.execute('SELECT * FROM JOBS WHERE lower(company) = ?;', (company_name.lower(),))
    return len(list(results))


# works if user does SELECT * from JOBS, takes the tuple data then makes a dictionary with the right keys
def process_db_job_data(job: Tuple):
    job_data = {'title': job[1], 'job_type': job[2], 'company': job[3], 'location': job[4],
                'description': job[5], 'url': job[7], 'created_at': job[8], 'how_to_apply_info': job[9],
                'company_logo_url': job[10], 'company_url': job[11], 'additional_info': job[12]}
    return job_data


def process_db_job_cache(job: Tuple):
    job_data = {'title': job[1], 'company': job[2], 'description': job[3], 'lat': job[4], 'lon': job[5]}
    return job_data