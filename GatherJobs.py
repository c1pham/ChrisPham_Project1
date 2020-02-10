import requests
import time
import sqlite3
from typing import Tuple
from typing import List


# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request
# https://www.btelligent.com/en/blog/best-practice-for-sql-statements-in-python/
# reference for parametrised queries


def main():  # collect jobs from github jobs API and store into text file
    db_connection, db_cursor = open_db("jobs_db")
    create_jobs_table(db_cursor)
    jobs = []  # hold jobs
    jobs = get_jobs(jobs)
    save_git_jobs_to_db(db_cursor, jobs)
    close_db(db_connection)


def get_jobs(all_jobs: List) -> List:
    # Link to API that retrieves job posting data
    git_jobs_url = "https://jobs.github.com/positions.json?"
    page_num = 1
    # retrieves about 5 pages, puts all jobs in the job list
    more_jobs = True
    while more_jobs:
        parameters = {'page': page_num}  # param to get jobs from a specific page
        req = requests.get(url=git_jobs_url, params=parameters)  # get jobs
        if str(req) != "<Response [503]>":  # if message is not 503, then convert to json and print
            jobs_from_api = req.json()
            all_jobs.extend(jobs_from_api)  # move jobs from api list to job list
            time.sleep(.1)
            page_num = page_num + 1  # if successful then increment page counter
            if len(jobs_from_api) < 50:  # if the length of the job page is less than 50 then it is last page
                more_jobs = False
    return all_jobs


def write_jobs_to_file(all_jobs, file_name: str):  # write dictionary objects into file
    writing_file = open(file_name, 'w')
    print(all_jobs, file=writing_file)  # write whole list to file
    writing_file.close()  # close so the file will save


def save_git_jobs_to_db(db_cursor: sqlite3.Cursor, all_jobs: List):
    for entry in all_jobs:  # go through each job posting and then add it to database table
        add_job_to_db(db_cursor, entry['title'], entry['type'], entry['company'], entry['location'],
                      entry['description'], api_id=entry['id'], url=entry['url'], created_at=entry['created_at'],
                      apply_url=entry['how_to_apply'], logo_url=entry['company_logo'], company_url=entry['company_url'])


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
    job_type TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    api_id TEXT,
    url TEXT,
    created_at TEXT,
    how_to_apply_url TEXT,
    company_logo_url TEXT,
    company_url TEXT,
    additional_info TEXT
    );''')


# this function is used to save individual jobs to database
def add_job_to_db(cursor: sqlite3.Cursor, title, job_type, company, location, description, api_id=None, url=None,
                  created_at=None, apply_url=None, logo_url=None, company_url=None, additional_info=None):
    #  data to be entered
    data = (title, job_type, company, location, description, api_id, url, created_at, apply_url, logo_url, company_url,
            additional_info)
    # SQL statement to insert data into jobs table
    sql_statement = '''INSERT INTO JOBS (title, job_type, company, location, description, api_id, url, created_at,
    how_to_apply_url, company_logo_url, company_url, additional_info)  VALUES (?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    # insert new entry to table
    cursor.execute(sql_statement, data)


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
