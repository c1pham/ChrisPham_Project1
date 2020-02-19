import GatherJobs
import os.path
import pytest


# https://pythonexamples.org/python-sqlite3-check-if-table-exists/
# this is website where I learned SQL command to check if it exist


# runs before everything to pass processed github job data and to functions that need it
@pytest.fixture
def get_github_data():
    import GatherJobs  # this runs independently of everything else before code is run so we import here
    all_jobs = GatherJobs.get_github_jobs()  # get jobs from API
    processed_jobs = GatherJobs.process_all_github_jobs(all_jobs)
    return processed_jobs


# runs before everything to pass processed stack overflow job data and to functions that need it
@pytest.fixture
def get_stack_overflow_data():
    import GatherJobs  # this runs independently of everything else before code is run so we import here
    all_jobs = GatherJobs.get_stack_overflow_jobs()  # get jobs from rss feed
    processed_jobs = GatherJobs.process_all_stack_overflow_jobs(all_jobs)
    return processed_jobs


# test to see if github data is downloading correctly
def test_getting_github_github_jobs(get_github_data):
    jobs = get_github_data  # get jobs from API
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


# test to see if stack overflow data is downloading correctly
def test_getting_stack_overflow_github_jobs(get_stack_overflow_data):
    jobs = get_stack_overflow_data  # get jobs from API
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


# checks to see if appropriate number of jobs save from github data
def test_save_all_github_jobs_to_db(get_github_data):
    db_connection, db_cursor = GatherJobs.open_db("all_github_jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_github_data  # hold jobs
    num_jobs_from_api = len(all_jobs)
    # num of jobs before programed save new jobs to db
    num_db_jobs_before_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))
    GatherJobs.save_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("all_github_jobs_db")
    # checks how many jobs in db after new jobs are saved
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    GatherJobs.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save - num_db_jobs_before_save


# checks to see if appropriate number of jobs save from stack overflow data
def test_save_all_stack_overflow_jobs_to_db(get_stack_overflow_data):
    db_connection, db_cursor = GatherJobs.open_db("all_stack_overflow_jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_stack_overflow_data  # hold jobs
    num_jobs_from_api = len(all_jobs)
    # num of jobs before programed save new jobs to db
    num_db_jobs_before_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))
    GatherJobs.save_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("all_stack_overflow_jobs_db")
    # checks how many jobs in db after new jobs are saved
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    GatherJobs.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save - num_db_jobs_before_save


#  checks to see if specific job saved with good data
def test_save_specific_github_job_to_db_good_data(get_github_data):
    #  set up database and save the jobs to the data base
    db_connection, db_cursor = GatherJobs.open_db("jobs_save_good_data_db")
    GatherJobs.create_jobs_table(db_cursor)
    all_jobs = get_github_data  # hold jobs from Github jobs API
    GatherJobs.save_jobs_to_db(db_cursor, all_jobs)
    GatherJobs.close_db(db_connection)
    # reopen db and check to see if first entry is in it
    db_connection, db_cursor = GatherJobs.open_db("jobs_save_good_data_db")
    job_name = all_jobs[0]['title']  # this is title of 1st job from github jobs API
    result = db_cursor.execute("SELECT * FROM JOBS WHERE title = ?;", (job_name,))
    num_results = len(list(result))
    GatherJobs.close_db(db_connection)  # close db connection
    assert num_results >= 1


#  checks to see if bad data is rejected from data base
def test_save_specific_github_job_to_db_bad_data():
    db_connection, db_cursor = GatherJobs.open_db("jobs_save_bad_github_data_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)

    all_jobs = GatherJobs.get_github_jobs()  # get jobs from API
    for key in all_jobs[0]:
        all_jobs[0][key] = None
    location = "Boston"
    all_jobs[0]['location'] = location
    # we reject data that does not have an title. the processing function if it managed to go by would
    # make it set to not provided
    results_not_provided_before_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                           ("NOT PROVIDED", location))
    results_none_data_before_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                        (None, location))
    # number of this entry before saving it for titles with either "not provided" or None data stored
    num_results_not_provided_before_saving = len(list(results_not_provided_before_saving))
    num_results_none_data_before_saving = len(list(results_none_data_before_saving))

    GatherJobs.add_job_to_db(db_cursor, GatherJobs.process_github_job(all_jobs[0]))
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_save_bad_github_data_db")
    # if the results should be same since the save to the processing function will return false
    # then the db saving function will reject false data
    results_not_provided_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                          ("NOT PROVIDED", location))
    results_none_data_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                       (None, location))
    # number of this entry after saving it for titles with either "not provided" or None data stored
    num_results_not_provided_after_saving = len(list(results_not_provided_after_saving))
    num_results_none_data_after_saving = len(list(results_none_data_after_saving))
    GatherJobs.close_db(db_connection)
    assert num_results_not_provided_after_saving == num_results_not_provided_before_saving
    assert num_results_none_data_after_saving == num_results_none_data_before_saving
    # if the number of results did not increased after saving, we know we rejected the data


# checks to see if bad data is rejected from database
def test_save_specific_stack_overflow_job_to_db_bad_data():
    db_connection, db_cursor = GatherJobs.open_db("jobs_save_stack_overflow_bad_data_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)

    all_jobs = GatherJobs.get_stack_overflow_jobs()  # get jobs from API
    for key in all_jobs[0]:
        all_jobs[0][key] = None
    # we reject data that does not have an title. the processing function if it managed to go by would
    # make it set to not provided
    results_not_provided_before_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                           ("NOT PROVIDED", "NOT PROVIDED"))
    results_none_data_before_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                        (None, None))
    # number of this entry of title with not provided before saving it
    num_results_not_provided_before_saving = len(list(results_not_provided_before_saving))
    num_results_none_data_before_saving = len(list(results_none_data_before_saving))
    GatherJobs.add_job_to_db(db_cursor, GatherJobs.process_stack_overflow_job(all_jobs[0]))
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_save_stack_overflow_bad_data_db")
    # if the results should be same since the save to the processing function will return false
    # then the db saving function will reject false data
    results_not_provided_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                          ("NOT PROVIDED", "NOT PROVIDED"))
    results_none_data_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                       (None, None))
    num_results_not_provided_after_saving = len(list(results_not_provided_after_saving))
    num_results_none_data_after_saving = len(list(results_none_data_after_saving))
    GatherJobs.close_db(db_connection)
    assert num_results_not_provided_after_saving == num_results_not_provided_before_saving
    assert num_results_none_data_before_saving == num_results_none_data_after_saving
    # if the number of results did not increased after saving, we know we rejected the data


# checks to see if table exist after program runs
def test_create_table():
    db_connection, db_cursor = GatherJobs.open_db("jobs_table_db")
    GatherJobs.create_jobs_table(db_cursor)
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_table_db")
    GatherJobs.create_jobs_table(db_cursor)
    result = db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='jobs';")
    all_result = list(result)  # this takes the sql data from cursor and turn into a list
    GatherJobs.close_db(db_connection)
    # the data from sql in the 0 slot is a tuple
    # and the only item in the tuple is a count of how many tables have that name
    num_matches = all_result[0][0]
    assert num_matches == 1  # if that count is 1 then table is successfully created


# checks to see if database exist
def test_making_db():
    db_connection, db_cursor = GatherJobs.open_db("jobs_test_db")  # this will make database if it does not exist
    GatherJobs.close_db(db_connection)
    file_exist = os.path.exists("jobs_test_db")  # returns true if this file exist
    assert file_exist is True  # pass test if it is true this file exists
