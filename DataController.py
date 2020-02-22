from urllib.error import HTTPError
import pandas
from typing import List
from typing import Dict
from typing import Tuple
import sqlite3
import geopy
from geotext import GeoText
import numpy
from geopy.exc import GeocoderQuotaExceeded


# https://www.btelligent.com/en/blog/best-practice-for-sql-statements-in-python/
# reference for parametrised queries
# https://pypi.org/project/geopy/
# reference for geopy documentation
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
# reference to learn pandas, code is not copied but just used for referenced


# create data frame for plotly to plot on map, has 4 columns, title, latitude, longitude, additional info
def process_job_data_into_data_frame(cursor: sqlite3.Cursor, job_data: List) -> pandas.DataFrame:
    all_jobs = []
    # cols for data frame
    columns = ['title', 'lat', 'lon', 'tags']
    # cache of all locations already requested and successful returned answer
    locations_tried = load_location_cache(cursor)
    for job in job_data:
        location = job['location']
        # keeps if location has already been requested
        if location in locations_tried:
            # grab location then make array for numpy array and add to all all jobs
            coordinates = locations_tried[location]
            current_job_data = [job['title'], coordinates[0], coordinates[1], job['additional_info']]
            all_jobs.append(current_job_data)
        else:
            # if not in location tried make new request
            coordinates = get_lat_long_coordinates_from_address(location)
            if coordinates is None:
                # if we can't get address from current string try to get cities with geo text then add
                cities = GeoText(location).cities
                for city in cities:
                    if city in locations_tried:
                        print(city)
                        coordinates = locations_tried[city]
                        current_job_data = [job['title'], coordinates[0], coordinates[1], job['additional_info']]
                        all_jobs.append(current_job_data)
                    else:
                        coordinates = get_lat_long_coordinates_from_address(city)
                        if coordinates is None:
                            # if no coordinates is given skip
                            continue
                        elif coordinates is not False:
                            locations_tried[coordinates[0]] = (coordinates[1], coordinates[2])
                            current_job_data = [job['title'], coordinates[1], coordinates[2], job['additional_info']]
                            all_jobs.append(current_job_data)
            elif coordinates is not False:
                locations_tried[coordinates[0]] = (coordinates[1], coordinates[2])
                current_job_data = [job['title'], coordinates[1], coordinates[2], job['additional_info']]
                all_jobs.append(current_job_data)
            else:
                print("http error")
                # this means error
    add_all_locations_to_db(cursor, locations_tried)
    numpy_array = numpy.array(all_jobs)
    data_frame = pandas.DataFrame(numpy_array, columns=columns)
    data_frame['lat'] = data_frame['lat'].astype(float)
    data_frame['lon'] = data_frame['lon'].astype(float)
    return data_frame


# takes all stack overflow data and makes a list of dictionaries to ready data for save to db function
def process_all_stack_overflow_jobs(all_jobs):
    processed_jobs = []
    for job in all_jobs:
        processed_job = process_stack_overflow_job(job)
        if processed_jobs is False:
            pass
        processed_jobs.append(processed_job)
    return processed_jobs


# process data from stack overflow
def process_stack_overflow_job(job_data: Dict) -> Dict:
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
        tags_into_database = "tags: "
        for tag in tags:
            tags_into_database += " " + tag['term']
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


def create_location_cache_table(db_cursor: sqlite3.Cursor):
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS locations_cache(
    location TEXT NOT NULL,
    latitude TEXT NOT NULL,
    longitude TEXT NOT NULL
    );''')


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
            month = str(months.index(time_data) + 1)
            if len(month) == 1:
                month = "0" + month
            date_dict['month'] = month
        elif len(time_data) == 4:  # if length is 4 then it is the year
            date_dict['year'] = time_data
        elif len(time_data) == 2:  # if length is 2 then it most likely the day
            if time_data[0] in tens_digits and time_data[1] in ones_digits:
                date_dict['day'] = time_data
    return date_dict['year'] + "-" + date_dict['month'] + "-" + date_dict['day']


def get_lat_long_coordinates_from_address(address: str):
    geo_locator = geopy.geocoders.Nominatim(user_agent="ChrisPham_Project1")
    location = None
    try:
        location = geo_locator.geocode(address, timeout=600)
    except HTTPError:
        return False
    except GeocoderQuotaExceeded:
        return False

    print(location)
    if location is None:
        print(address + " could not find location")
        return None

    return address, location.latitude, location.longitude


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


def get_all_company_jobs(all_jobs: List, company_name: str) -> List:
    all_company_jobs = []
    for job in all_jobs:
        company = job['company'].lower()
        if company == company_name.lower():
            all_company_jobs.append(job)
    return all_company_jobs


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


# works if user does SELECT * from JOBS, takes the tuple data then makes a dictionary with the right keys
def process_db_job_data(job: Tuple):
    job_data = {'title': job[1], 'job_type': job[2], 'company': job[3], 'location': job[4],
                'description': job[5], 'url': job[7], 'created_at': job[8], 'how_to_apply_info': job[9],
                'company_logo_url': job[10], 'company_url': job[11], 'additional_info': job[12]}
    return job_data
