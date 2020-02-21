import pandas
from typing import List
from typing import Dict
from typing import Tuple
import sqlite3
import geopy
import numpy
import JobCollector

# https://www.btelligent.com/en/blog/best-practice-for-sql-statements-in-python/
# reference for parametrised queries
# https://pypi.org/project/geopy/
# reference for geopy documentation
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
# reference to learn pandas, code is not copied but just used for referenced


def main():
    all_jobs = JobCollector.get_stack_overflow_jobs()
    processed_jobs = process_all_stack_overflow_jobs(all_jobs)
    nonremote_jobs = get_all_non_remote_jobs(processed_jobs)
    data_for_plotly = process_job_data_into_dataframe(nonremote_jobs)
    print(data_for_plotly)


def process_job_data_into_dataframe(job_data: List) -> pandas.DataFrame :
    all_jobs = []
    columns = ['title', 'lat', 'long']
    for job in job_data:
        location = job['location']
        coordinates = get_lat_long_coordinates_from_address(location)
        current_job_data = [job['title'], coordinates[0], coordinates[1], job['additional_info']]
        all_jobs.append(current_job_data)
    numpy_array = numpy.array(all_jobs)
    return pandas.DataFrame(numpy_array, columns=columns)


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


# this function is used to save individual jobs to database
def add_job_to_db(cursor: sqlite3.Cursor, job_data: Dict):
    if job_data is False:
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


# go through a string for time and returns a string for time in the month day and year format
def parse_date(date: str) -> str:
    date_dict = {}
    months = ["Jan", "Feb", "Mar", "Apr", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ones_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    tens_digits = ['0', '1', '2', '3']
    date_parts = date.split(" ")

    for time_data in date_parts:
        if time_data in months:
            date_dict['month'] = str(months.index(time_data) + 1)
        elif len(time_data) == 4:  # if length is 4 then it is the year
            date_dict['year'] = time_data
        elif len(time_data) == 2:  # if length is 2 then it most likely the day
            if time_data[0] in tens_digits and time_data[1] in ones_digits:
                date_dict['day'] = time_data
    return date_dict['month'] + "-" + date_dict['day'] + "-" + date_dict['year']


def get_lat_long_coordinates_from_address(address: str) -> Tuple:
    geo_locator = geopy.geocoders.Nominatim(user_agent="ChrisPham_Project1")
    location = geo_locator.geocode(address)
    print(location)
    return location.latitude, location.longitude


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


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
