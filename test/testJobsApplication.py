import JobCollector
import os.path
import pytest
import DataController
import App
import ssl


# https://pythonexamples.org/python-sqlite3-check-if-table-exists/
# this is website where I learned SQL command to check if it exist


# runs before everything to pass processed github job data and to functions that need it
@pytest.fixture
def get_github_data():
    import JobCollector  # this runs independently of everything else before code is run so we import here
    all_jobs = JobCollector.get_github_jobs()  # get jobs from API
    processed_jobs = DataController.process_all_github_jobs(all_jobs)
    return processed_jobs


# runs before everything to pass processed stack overflow job data and to functions that need it
@pytest.fixture
def get_stack_overflow_data():
    import JobCollector  # this runs independently of everything else before code is run so we import here
    all_jobs = JobCollector.get_stack_overflow_jobs()  # get jobs from rss feed
    processed_jobs = DataController.process_all_stack_overflow_jobs(all_jobs)
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
    db_connection, db_cursor = DataController.open_db("all_github_jobs_db")  # open db
    db_cursor.execute("DROP TABLE IF EXISTS JOBS;")
    DataController.create_jobs_table(db_cursor)
    all_jobs = get_github_data  # hold jobs
    num_jobs_from_api = len(all_jobs)
    # num of jobs before programed save new jobs to db
    DataController.save_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    DataController.close_db(db_connection)

    db_connection, db_cursor = DataController.open_db("all_github_jobs_db")
    # checks how many jobs in db after new jobs are saved
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    DataController.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save


# checks to see if appropriate number of jobs save from stack overflow data
def test_save_all_stack_overflow_jobs_to_db(get_stack_overflow_data):
    db_connection, db_cursor = DataController.open_db("all_stack_overflow_jobs_db")  # open db
    db_cursor.execute("DROP TABLE IF EXISTS JOBS;")
    DataController.create_jobs_table(db_cursor)
    all_jobs = get_stack_overflow_data  # hold jobs
    num_jobs_from_api = len(all_jobs)
    # num of jobs before programed save new jobs to db

    DataController.save_jobs_to_db(db_cursor, all_jobs)  # add new jobs to db
    DataController.close_db(db_connection)

    db_connection, db_cursor = DataController.open_db("all_stack_overflow_jobs_db")
    # checks how many jobs in db after new jobs are saved
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    DataController.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save


#  checks to see if specific job saved with good data
def test_save_specific_github_job_to_db_good_data(get_github_data):
    #  set up database and save the jobs to the data base
    db_connection, db_cursor = DataController.open_db("jobs_save_good_data_db")
    DataController.create_jobs_table(db_cursor)
    all_jobs = get_github_data  # hold jobs from Github jobs API
    DataController.save_jobs_to_db(db_cursor, all_jobs)
    DataController.close_db(db_connection)
    # reopen db and check to see if first entry is in it
    db_connection, db_cursor = DataController.open_db("jobs_save_good_data_db")
    job_name = all_jobs[0]['title']  # this is title of 1st job from github jobs API
    result = db_cursor.execute("SELECT * FROM JOBS WHERE title = ?;", (job_name,))
    num_results = len(list(result))
    DataController.close_db(db_connection)  # close db connection
    assert num_results >= 1


#  checks to see if bad data is rejected from data base
def test_save_specific_github_job_to_db_bad_data():
    db_connection, db_cursor = DataController.open_db("jobs_save_bad_github_data_db")  # open db
    DataController.create_jobs_table(db_cursor)

    all_jobs = JobCollector.get_github_jobs()  # get jobs from API
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

    DataController.add_job_to_db(db_cursor, DataController.process_github_job(all_jobs[0]))
    DataController.close_db(db_connection)

    db_connection, db_cursor = DataController.open_db("jobs_save_bad_github_data_db")
    # if the results should be same since the save to the processing function will return false
    # then the db saving function will reject false data
    results_not_provided_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                          ("NOT PROVIDED", location))
    results_none_data_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                       (None, location))
    # number of this entry after saving it for titles with either "not provided" or None data stored
    num_results_not_provided_after_saving = len(list(results_not_provided_after_saving))
    num_results_none_data_after_saving = len(list(results_none_data_after_saving))
    DataController.close_db(db_connection)
    assert num_results_not_provided_after_saving == num_results_not_provided_before_saving
    assert num_results_none_data_after_saving == num_results_none_data_before_saving
    # if the number of results did not increased after saving, we know we rejected the data


# checks to see if bad data is rejected from database
def test_save_specific_stack_overflow_job_to_db_bad_data():
    db_connection, db_cursor = DataController.open_db("jobs_save_stack_overflow_bad_data_db")  # open db
    DataController.create_jobs_table(db_cursor)

    all_jobs = JobCollector.get_stack_overflow_jobs()  # get jobs from API
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
    DataController.add_job_to_db(db_cursor, DataController.process_stack_overflow_job(all_jobs[0]))
    DataController.close_db(db_connection)

    db_connection, db_cursor = DataController.open_db("jobs_save_stack_overflow_bad_data_db")
    # if the results should be same since the save to the processing function will return false
    # then the db saving function will reject false data
    results_not_provided_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                          ("NOT PROVIDED", "NOT PROVIDED"))
    results_none_data_after_saving = db_cursor.execute("SELECT * FROM JOBS WHERE title=? AND location=?;",
                                                       (None, None))
    num_results_not_provided_after_saving = len(list(results_not_provided_after_saving))
    num_results_none_data_after_saving = len(list(results_none_data_after_saving))
    DataController.close_db(db_connection)
    assert num_results_not_provided_after_saving == num_results_not_provided_before_saving
    assert num_results_none_data_before_saving == num_results_none_data_after_saving
    # if the number of results did not increased after saving, we know we rejected the data


# checks to see if table exist after program runs
def test_create_table():
    db_connection, db_cursor = DataController.open_db("jobs_table_db")
    DataController.create_jobs_table(db_cursor)
    DataController.close_db(db_connection)

    db_connection, db_cursor = DataController.open_db("jobs_table_db")
    DataController.create_jobs_table(db_cursor)
    result = db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='jobs';")
    all_result = list(result)  # this takes the sql data from cursor and turn into a list
    DataController.close_db(db_connection)
    # the data from sql in the 0 slot is a tuple
    # and the only item in the tuple is a count of how many tables have that name
    num_matches = all_result[0][0]
    assert num_matches == 1  # if that count is 1 then table is successfully created


# checks to see if database exist
def test_making_db():
    db_connection, db_cursor = DataController.open_db("jobs_test_db")  # this will make database if it does not exist
    DataController.close_db(db_connection)
    file_exist = os.path.exists("jobs_test_db")  # returns true if this file exist
    assert file_exist is True  # pass test if it is true this file exists


# test to see if company filter successful gets the jobs with the right company
def test_company_filter_good_data():
    google_job = {'title': "Web Dev", 'job_type': "Full Time", 'company': "Google", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    facebook_job = {'title': "Web Dev", 'job_type': "Full Time", 'company': "Facebook", 'location': "Spain",
                    'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                    'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                    'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    amazon_job = {'title': "Web Dev", 'job_type': "Full Time", 'company': "Amazon", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                  'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    test_jobs = [google_job, facebook_job, amazon_job]
    company_to_get = "Google"
    # only one of these jobs have google for company so the length of company jobs should be 1
    company_jobs = App.filter_jobs_with_company(test_jobs, company_to_get)
    assert len(company_jobs) == 1


def test_company_filter_bad_data():
    irobot_job = {'title': "Engineer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    facebook_job = {'title': "Tech Manager", 'job_type': "Full Time", 'company': "Facebook", 'location': "Spain",
                    'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                    'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                    'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    amazon_job = {'title': "Senior engineer", 'job_type': "Full Time", 'company': "Amazon", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                  'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    test_jobs = [irobot_job, facebook_job, amazon_job]
    company_to_get = "Google"
    # none of these jobs companies are google so the next func should return false meaning empty list
    company_jobs = App.filter_jobs_with_company(test_jobs, company_to_get)
    # get_all_company_jobs return false if empty list
    assert company_jobs is False


# this test what happens when the user puts in a title that is not in the data base
def test_title_filter_bad_data():
    irobot_job = {'title': "Web Dev", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    facebook_job = {'title': "Tech Lead", 'job_type': "Full Time", 'company': "Facebook", 'location': "Spain",
                    'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                    'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                    'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    amazon_job = {'title': "Senior Tech Lead", 'job_type': "Full Time", 'company': "Amazon", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                  'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    test_jobs = [irobot_job, facebook_job, amazon_job]
    title_to_get = "Non-Existent-Job-Title"
    jobs_with_title = App.filter_jobs_with_company(test_jobs, title_to_get)
    # title filter return false if it ends up with empty list
    assert jobs_with_title is False


# test title filter to see if it works to get appropriate number of jobs with correct title
# this matches jobs with the user input somewhere in the title
def test_title_filter_good_data():
    irobot_job = {'title': "Solutions Manager", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    facebook_job = {'title': "IT Manager", 'job_type': "Full Time", 'company': "Facebook", 'location': "Spain",
                    'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                    'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                    'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    amazon_job = {'title': "Tech Lead", 'job_type': "Full Time", 'company': "Amazon", 'location': "Spain",
                  'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "www.facebook.com",
                  'company_logo_url': "facebook.com", 'company_url': "facebook", 'additional_info': "javascript"}
    test_jobs = [irobot_job, facebook_job, amazon_job]
    title_to_get = "Solutions Manager"
    jobs_with_title = App.filter_jobs_with_title(test_jobs, title_to_get)
    # title filter return false if it ends up with empty list
    assert len(jobs_with_title) == 1


# this test to see if time filter can get the appropriate on or after an specified date
def test_time_filter_good_data():
    time_connection, time_cursor = DataController.open_db("good_time_db")
    time_cursor.execute("DROP TABLE IF EXISTS JOBS;")
    DataController.create_jobs_table(time_cursor)
    # only 2 of these jobs should be returned by filter function
    good_time_robot_job = {'title': "Solutions Manager", 'job_type': "Full Time", 'company': "iRobot",
                           'location': "Spain",
                           'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                           'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                           'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    good_time_web_job = {'title': "Web", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                         'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
                         'created_at': "Wed, 12 Feb 2020 20:55:54 Z", 'how_to_apply_info': "google.com",
                         'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    bad_time_job = {'title': "Solutions Manager", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                    'description': "Develop websites", 'api_id': "12346", 'url': "www.apply.com",
                    'created_at': "Wed, 12 Feb 2005 20:55:54 Z", 'how_to_apply_info': "google.com",
                    'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    test_jobs = [good_time_robot_job, good_time_web_job, bad_time_job]
    DataController.save_jobs_to_db(time_cursor, test_jobs)
    DataController.close_db(time_connection)
    time_connection, time_cursor = DataController.open_db("good_time_db")
    time = '2005-04-01'
    # find jobs that were created on or after specified date which should be 2
    jobs_with_time = App.filter_jobs_with_time(time_cursor, time)
    assert len(jobs_with_time) == 2


# this test what happens when the user puts in a time that is beyond today so no jobs should be found
def test_time_filter_bad_data():
    time_connection, time_cursor = DataController.open_db("bad_time_db")
    time_cursor.execute("DROP TABLE IF EXISTS JOBS;")
    DataController.create_jobs_table(time_cursor)
    bad_time_robot_job = {'title': "Solutions Manager", 'job_type': "Full Time", 'company': "iRobot",
                          'location': "Spain",
                          'description': "Develop websites", 'api_id': "1234", 'url': "www.apply.com",
                          'created_at': "Wed, 12 Feb 2010 20:55:54 Z", 'how_to_apply_info': "google.com",
                          'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    bad_time_web_job = {'title': "Web", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                        'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
                        'created_at': "Wed, 12 Feb 2000 20:55:54 Z", 'how_to_apply_info': "google.com",
                        'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    bad_time_manager_job = {'title': "Solutions Manager", 'job_type': "Full Time", 'company': "iRobot",
                            'location': "Spain", 'description': "Develop websites", 'api_id': "12346",
                            'url': "www.apply.com", 'created_at': "Wed, 12 Feb 2015 20:55:54 Z",
                            'how_to_apply_info': "google.com", 'company_logo_url': "google.com",
                            'company_url': "google", 'additional_info': "javascript"}
    test_jobs = [bad_time_robot_job, bad_time_web_job, bad_time_manager_job]
    DataController.save_jobs_to_db(time_cursor, test_jobs)
    DataController.close_db(time_connection)
    time_connection, time_cursor = DataController.open_db("bad_time_db")
    time = '2021-04-01'

    jobs_with_time = App.filter_jobs_with_time(time_cursor, time)
    # if the previous function returns false that means no jobs were found after the time we searched for
    assert jobs_with_time is False


# test to see if the filter can get the appropriate jobs
def test_technology_filter_good_data():
    web_angular_job = {'title': "Angular Developer", 'job_type': "Full Time", 'company': "iRobot",
                       'location': "Spain",
                       'description': "Use Angular", 'api_id': "1234", 'url': "www.apply.com",
                       'created_at': "Wed, 12 Feb 2010 20:55:54 Z", 'how_to_apply_info': "google.com",
                       'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "angular"}
    web_job = {'title': "Full Stack Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
               'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
               'created_at': "Wed, 12 Feb 2000 20:55:54 Z", 'how_to_apply_info': "google.com",
               'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    python_job = {'title': "Python Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                  'description': "Develop python programs", 'api_id': "12346", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2015 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "Python"}
    test_jobs = [web_angular_job, web_job, python_job]
    # these tags are in 2 out of 3 of the jobs
    tech_jobs = App.filter_jobs_with_technology(test_jobs, "Web", "Javascript", "Angular")
    assert len(tech_jobs) == 2


# test to see what happens if the user puts in technology that won't match the jobs and if they leave a input box empty
def test_technology_filter_bad_data():
    web_angular_job = {'title': "MongoDB Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                       'description': "Use Angular", 'api_id': "1234", 'url': "www.apply.com",
                       'created_at': "Wed, 12 Feb 2010 20:55:54 Z", 'how_to_apply_info': "google.com",
                       'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "angular"}
    web_job = {'title': "Stack Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
               'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
               'created_at': "Wed, 12 Feb 2000 20:55:54 Z", 'how_to_apply_info': "google.com",
               'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    python_job = {'title': "Junior Python Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                  'description': "Develop python programs", 'api_id': "12346", 'url': "www.apply.com",
                  'created_at': "Wed, 12 Feb 2015 20:55:54 Z", 'how_to_apply_info': "google.com",
                  'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "Python"}
    test_jobs = [web_angular_job, web_job, python_job]
    # none of these are in job title description of additional info, and we pass in empty string
    tech_jobs = App.filter_jobs_with_technology(test_jobs, "JSON", "SQL", "")
    # the previous func returns false is no jobs match
    assert tech_jobs is False


# this function test to see if we will get the two boston jobs we want, with all the appropriate data we want
# the reason why this function is like this is to find jobs by lat lon is because the plotly map will return click data
# for the plots the user press that always have some information in it
def test_selected_jobs_good_data():
    ssl._create_default_https_context = ssl._create_unverified_context
    boston_robot_job = {'title': "MongoDB Developer", 'job_type': "Full Time", 'company': "iRobot",
                        'location': "Boston MA", 'description': "Use Angular", 'api_id': "1234", 'url': "www.apply.com",
                        'created_at': "Wed, 12 Feb 2010 20:55:54 Z", 'how_to_apply_info': "google.com",
                        'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "angular"}
    boston_web_job = {'title': "Stack Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Boston MA",
                      'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
                      'created_at': "Wed, 12 Feb 2000 20:55:54 Z", 'how_to_apply_info': "google.com",
                      'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    spain_job = {'title': "Junior Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                 'description': "Develop python programs", 'api_id': "12346", 'url': "www.apply.com",
                 'created_at': "Wed, 12 Feb 2015 20:55:54 Z", 'how_to_apply_info': "google.com",
                 'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "Python"}
    all_jobs = [boston_robot_job, boston_web_job, spain_job]

    jobs = selected_jobs_func(all_jobs, "Boston MA")
    # job information to be compared
    robot_description = boston_robot_job['description']
    robot_title = boston_robot_job['title']
    robot_company = boston_robot_job['company']
    web_description = boston_web_job['description']
    web_title = boston_web_job['title']
    web_company = boston_web_job['company']

    count = 0
    # check to see if the jobs from the function are the two we had earlier by comparing the data
    for job in jobs:
        if job['title'] == web_title and job['description'] == web_description and job['company'] == web_company:
            count += 1
        elif job['title'] == robot_title and job['description'] == robot_description and\
                job['company'] == robot_company:
            count += 1

    assert count == 2  # if count is 2 we know there the jobs we want in the database


# this function will test what happens if a lat lon coordinate is used that is not in the dbs table
def test_selected_jobs_bad_data():
    ssl._create_default_https_context = ssl._create_unverified_context
    boston_robot_job = {'title': "MongoDB Developer", 'job_type': "Full Time", 'company': "iRobot",
                        'location': "Boston MA", 'description': "Use Angular", 'api_id': "1234", 'url': "www.apply.com",
                        'created_at': "Wed, 12 Feb 2010 20:55:54 Z", 'how_to_apply_info': "google.com",
                        'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "angular"}
    boston_web_job = {'title': "Stack Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Boston MA",
                      'description': "Develop websites", 'api_id': "12345", 'url': "www.apply.com",
                      'created_at': "Wed, 12 Feb 2000 20:55:54 Z", 'how_to_apply_info': "google.com",
                      'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "javascript"}
    spain_job = {'title': "Junior Developer", 'job_type': "Full Time", 'company': "iRobot", 'location': "Spain",
                 'description': "Develop python programs", 'api_id': "12346", 'url': "www.apply.com",
                 'created_at': "Wed, 12 Feb 2015 20:55:54 Z", 'how_to_apply_info': "google.com",
                 'company_logo_url': "google.com", 'company_url': "google", 'additional_info': "Python"}
    all_jobs = [boston_robot_job, boston_web_job, spain_job]
    # quincy is not in the job data so the lat lin will be different
    jobs = selected_jobs_func(all_jobs, "Quincy MA")
    # previous func returns false if the jobs returned have zero length
    assert jobs is False


# this function is here because two of the test being used are remarkably similiar for good data
# and bad data of making sure the selected job data match
def selected_jobs_func(all_jobs, test_address):
    job_db_connection, job_db_cursor = DataController.open_db("selected_jobs_db")
    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("selected_jobs_cache_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("selected_location_db")
    default_job_cache_db_connection, default_job_cache_db_cursor =\
        DataController.open_db("selected_default_jobs_cache_db")
    # drop tables because these databases are used in two test and we want a fresh table every time
    job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE;")
    default_job_cache_db_cursor.execute("DROP TABLE IF EXISTS JOBS_CACHE;")
    DataController.create_job_cache_table(job_cache_db_cursor)
    DataController.create_job_cache_table(default_job_cache_db_cursor)
    DataController.create_jobs_table(job_db_cursor)
    DataController.create_location_cache_table(loc_db_cursor)

    DataController.save_jobs_to_db(job_db_cursor, all_jobs)
    DataController.close_db(job_db_connection)
    job_db_connection, job_db_cursor = DataController.open_db("selected_jobs_db")
    # the data controller function will make a data frame but also save the jobs that are not remote the cache dbs
    jobs_from_db = DataController.load_jobs_from_db(job_db_cursor)
    DataController.process_job_data_into_data_frame(loc_db_cursor, jobs_from_db,
                                                    [job_cache_db_cursor, default_job_cache_db_cursor])

    connections = [job_cache_db_connection, job_db_connection, loc_db_connection, default_job_cache_db_connection]
    DataController.close_dbs(connections)

    job_cache_db_connection, job_cache_db_cursor = DataController.open_db("selected_jobs_cache_db")
    # this data is used to find jobs with matching lat and lon
    location_data = DataController.get_lat_lon_coordinates_from_address(test_address)
    lat = str(location_data[1])
    lon = str(location_data[2])
    jobs_cache = DataController.load_jobs_cache(job_cache_db_cursor)

    return DataController.get_jobs_from_cache_with_lat_long(jobs_cache, lat, lon)
