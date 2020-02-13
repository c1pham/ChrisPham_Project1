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
    create_github_jobs_table(db_cursor)
    jobs = []  # hold jobs
    jobs = get_jobs(jobs)
    processed_jobs = process_all_jobs(jobs)
    save_git_jobs_to_db(db_cursor, processed_jobs)
    close_db(db_connection)


def test():
    ssl._create_default_https_context = ssl._create_unverified_context
    raw_data = feedparser.parse('https://stackoverflow.com/jobs/feed')
    print(raw_data)
    print(raw_data.feed)
    for item in raw_data.entries:
        print(item)
    print(len(raw_data.entries))
    return raw_data.entries


def get_jobs(all_jobs: List) -> List[Dict]:
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
def process_all_jobs(all_jobs: List[Dict]) -> List[Dict]:
    processed_jobs = []
    for job in all_jobs:
        processed_job = process_job(job)
        processed_jobs.append(processed_job)
    return processed_jobs


# works ad adapter class, moves job data to a new dictionary
def process_job(job_data: Dict) -> Dict:
    processed_job = {}
    # keys that would be in dictionary
    job_keys = {'id': ['api_id'], 'type': ['job_type'], 'url': [], 'created_at': [], 'company': [], 'company_url': [],
                'location': [], 'title': [], 'description': [], 'how_to_apply': ["how_to_apply_url"],
                'company_logo': ['company_logo_url'], 'additional_info': []}
    # will go through each job and see if the key is in job keys, if so it will update the dictionary value
    for key in job_keys.keys():
        if key in job_data.keys():
            value = job_data[key]
            if value is not None:
                # check to see if key has value of length 1, that means they had a different column name
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = job_data[key]
                else:  # rest of other keys names match up to column names
                    processed_job[key] = job_data[key]
            else:  # if the value is null then replace it with not provided
                if len(job_keys[key]) == 1:
                    processed_job[job_keys[key][0]] = "NOT PROVIDED"
                else:
                    processed_job[key] = "NOT PROVIDED"
        else:  # if the key is not in the dictionary will make the add the key pair with the value of it not provided
            if len(job_keys[key]) == 1:
                processed_job[job_keys[key][0]] = "NOT PROVIDED"
            else:
                processed_job[key] = "NOT PROVIDED"
    return processed_job


def save_git_jobs_to_db(db_cursor: sqlite3.Cursor, all_jobs: List):
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
def create_github_jobs_table(db_cursor: sqlite3.Cursor):
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
    how_to_apply_url TEXT NOT NULL,
    company_logo_url TEXT,
    company_url TEXT,
    additional_info TEXT
    );''')


# this function is used to save individual jobs to database
def add_job_to_db(cursor: sqlite3.Cursor, preprocess_job_data: Dict):
    job_data = process_job(preprocess_job_data)
    #  data to be entered
    sql_data = (job_data['title'], job_data['job_type'], job_data['company'], job_data['location'],
                job_data['description'], job_data['api_id'], job_data['url'], job_data['created_at'],
                job_data['how_to_apply_url'], job_data['company_logo_url'], job_data['company_url'],
                job_data['additional_info'])
    # SQL statement to insert data into jobs table
    sql_statement = '''INSERT INTO JOBS (title, job_type, company, location, description, api_id, url, created_at,
    how_to_apply_url, company_logo_url, company_url, additional_info)  VALUES (?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    # insert new entry to table
    cursor.execute(sql_statement, sql_data)


if __name__ == '__main__':  # if running from this file, then run the main function
    # main()
    test()
