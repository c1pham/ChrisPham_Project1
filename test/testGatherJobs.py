import GatherJobs
import os.path
import pytest
# https://pythonexamples.org/python-sqlite3-check-if-table-exists/
# this is website where I learned SQL command to check if it exist


# runs before everything to pass job data to functions that need it
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


#  checks to see if specific job saved with good data
def test_save_specific_job_to_db_good_data(get_data):
    #  set up database and save the jobs to the data base
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_data  # hold jobs from Github jobs API
    GatherJobs.save_git_jobs_to_db(db_cursor, all_jobs)
    GatherJobs.close_db(db_connection)
    # reopen db and check to see if first entry is in it
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    job_name = all_jobs[0]['title']  # this is title of 1st job from github jobs API
    result = db_cursor.execute("SELECT * FROM JOBS WHERE title = ?;", (job_name,))
    num_results = len(list(result))
    GatherJobs.close_db(db_connection)  # close db connection
    assert num_results >= 1


#  checks to see how bad data saved to the database
def test_save_specific_job_to_db_bad_data(get_data):
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    job_data = get_data[0]
    # makes all the values in the job data None
    for key in job_data:
        job_data[key] = None
    fake_title = "FAKE SOFTWARE ENGINEERING TITLE NAME"
    job_data['title'] = fake_title  # make one entry with a fake unique name
    results_before_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                              (fake_title, "NOT PROVIDED"))
    num_results_before_saving = len(list(results_before_saving))  # number of this entry before saving it
    GatherJobs.add_job_to_db(db_cursor, job_data)
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    # if we saved data to handle null data, the null values were changed to NOT PROVIDED
    # we should also find at least one new entry
    results_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                         (fake_title, "NOT PROVIDED"))
    num_results_after_saving = len(list(results_after_saving))
    GatherJobs.close_db(db_connection)
    assert num_results_after_saving - num_results_before_saving == 1
    # if the number of results increased by 1 after saving, we saved correctly


# checks to see if table exist after program runs
def test_create_table():
    GatherJobs.main()  # run program
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
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
