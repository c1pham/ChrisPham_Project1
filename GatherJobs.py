import requests
import time
import sqlite3
from typing import Tuple
from typing import List
from typing import Dict
import feedparser
import ssl


# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request
# https://www.btelligent.com/en/blog/best-practice-for-sql-statements-in-python/
# reference for parametrised queries


def main():  # collect jobs from github jobs API and store into text file
    db_connection, db_cursor = open_db("jobs_db")
    create_jobs_table(db_cursor)
    github_jobs = []  # hold jobs
    github_jobs = get_github_jobs()
    stack_overflow_jobs = get_stack_overflow_jobs()

    processed_github_jobs = process_all_github_jobs(github_jobs)
    processed_stack_overflow_jobs = process_all_stack_overflow_jobs(stack_overflow_jobs)

    save_jobs_to_db(db_cursor, processed_github_jobs)
    save_jobs_to_db(db_cursor, processed_stack_overflow_jobs)

    close_db(db_connection)


def get_stack_overflow_jobs():
    ssl._create_default_https_context = ssl._create_unverified_context
    raw_data = feedparser.parse('https://stackoverflow.com/jobs/feed')
    return raw_data.entries


def process_all_stack_overflow_jobs(all_jobs):
    processed_jobs = []
    for job in all_jobs:
        processed_job = process_stack_overflow_job(job)
        if processed_jobs is False:
            pass
        processed_jobs.append(processed_job)
    return processed_jobs


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


def get_github_jobs() -> List[Dict]:
    all_jobs = []
    # Link to API that retrieves job posting data
    git_jobs_url = "https://jobs.github.com/positions.json?"
    page_num = 1
    # retrieves about 5 pages, puts all jobs in the job list
    more_jobs = True
    error_code_503_responses = 0
    while more_jobs and error_code_503_responses < 10:  # after 10 503 errors will stop requesting
        parameters = {'page': page_num}  # param to get jobs from a specific page
        req = requests.get(url=git_jobs_url, params=parameters)  # get jobs
        if str(req) != "<Response [503]>":  # if message is not 503, then convert to json and print
            jobs_from_api = req.json()
            all_jobs.extend(jobs_from_api)  # move jobs from api list to job list
            time.sleep(.1)
            page_num = page_num + 1  # if successful then increment page counter
            if len(jobs_from_api) < 50:  # if the length of the job page is less than 50 then it is last page
                more_jobs = False
        elif str(req) == "<Response [503]>":
            error_code_503_responses += 1
    return all_jobs


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
                job_data['description'], job_data['api_id'], job_data['url'], job_data['created_at'],
                job_data['how_to_apply_info'], job_data['company_logo_url'], job_data['company_url'],
                job_data['additional_info'])
    # SQL statement to insert data into jobs table
    sql_statement = '''INSERT INTO JOBS (title, job_type, company, location, description, api_id, url, created_at
    , how_to_apply_info, company_logo_url, company_url, additional_info)  VALUES (?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    # insert new entry to table
    cursor.execute(sql_statement, sql_data)


def parse_date(date: str) -> Dict:
    date_dict = {}
    #    months = ["Jan", "Feb", "Mar", "Apr", "June", "Jul", "Aug", "Oct", "Nov", "Dec"]
    date_parts = date.split(" ")
    date_dict["day"] = date_parts[1]
    date_dict["year"] = date_parts[4]


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
