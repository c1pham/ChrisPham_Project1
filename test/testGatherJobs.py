import GatherJobs
import os.path
import pytest
# https://pythonexamples.org/python-sqlite3-check-if-table-exists/
# this is website where I learned SQL command to check if it exist


@pytest.fixture
def get_data():
    import GatherJobs  # this runs independently of everything else before code is run so we import here
    all_jobs = []
    all_jobs = GatherJobs.get_jobs(all_jobs)  # get jobs from API
    processed_jobs = GatherJobs.process_all_jobs(all_jobs)
    return processed_jobs


def test_getting_jobs(get_data):
    jobs = get_data  # get jobs from API
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


# checks to see if appropriate number of jobs save and if a specific job I know is there saved
def test_save_all_jobs_to_db(get_data):
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_data  # hold jobs
    num_jobs_from_api = len(all_jobs)
    # num of jobs before programed save new jobs to db
    num_db_jobs_before_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))
    GatherJobs.save_git_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    # checks how many jobs in db after new jobs are saved
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    GatherJobs.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save - num_db_jobs_before_save


def test_save_specific_job_to_db_good_data(get_data):
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_data  # hold jobs from Github jobs API
    GatherJobs.save_git_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    job_name = all_jobs[1]['title']  # this is title of 1st job from github jobs API
    result = db_cursor.execute("SELECT * FROM JOBS WHERE title = ?;", (job_name,))
    num_results = len(list(result))
    GatherJobs.close_db(db_connection)  # close db connection
    assert num_results >= 1


#  def test_save_specific_job_to_db_bad_data():
#    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
#    GatherJobs.create_jobs_table(db_cursor)
#    fake_job_title = "Software Engineer NO WAY COULD BE JOB TITLE" + random.randint()
#    fake_job_company = "Stark Industries" + random.randint()
#    GatherJobs.add_job_to_db(db_cursor, fake_job_title, None, fake_job_company, None, None)
#    GatherJobs.close_db(db_connection)
#    bad_data = (fake_job_title, None, fake_job_company, None, None)
#    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
#    db_cursor.execute("SELECT * FROM JOBS WHERE ")


def test_create_table():
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)  # create table
    result = db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='jobs';")
    all_result = list(result)  # this takes the sql data from cursor and turn into a list
    GatherJobs.close_db(db_connection)
    # the data from sql in the 0 slot is a tuple
    # and the only item in the tuple is a count of how many tables have that name
    num_matches = all_result[0][0]
    assert num_matches == 1  # if that count is 1 then table is successfully created


# checks to see if database exist
def test_making_db():
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # this will make database if it does not exist
    GatherJobs.close_db(db_connection)
    file_exist = os.path.exists("jobs_db")  # returns true if this file exist
    assert file_exist is True  # pass test if it is true this file exists
