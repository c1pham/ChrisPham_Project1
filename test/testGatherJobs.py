import GatherJobs
# https://pythonexamples.org/python-sqlite3-check-if-table-exists/
# this is website where I learned SQL command to check if it exist


def test_getting_jobs():
    jobs = []
    jobs = GatherJobs.get_jobs(jobs)  # get jobs from API
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


# def test_write_file():
#    GatherJobs.main()
#    job_file = open("jobs.txt", 'r')
#    lines_in_file = job_file.readlines()
#    # this looks through the first line of document to find this job title because dump put all data in first line
#    # find will return -1 if the string is not in there
#    indicator = lines_in_file[0].find("(Senior-) Full Stack TypeScript Developer (m/w/d)")
#    # if the find function returns anything else than -1, meaning it return position of string then the test passed
#    assert indicator != 1


# checks to see if appropriate number of jobs save and if a specific job I know is there saved
def test_save_to_db():
    db_connection, db_cursor = GatherJobs.open_db("jobs_db")  # open db
    GatherJobs.create_jobs_table(db_cursor)
    jobs = []  # hold jobs
    jobs = GatherJobs.get_jobs(jobs)  # get jobs from Github jobs API
    num_jobs_from_api = len(jobs)
    # num of jobs before save new jobs to db
    num_db_jobs_before_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))
    GatherJobs.save_git_jobs_to_db(db_cursor, jobs)  # add new jobs to db
    GatherJobs.close_db(db_connection)

    db_connection, db_cursor = GatherJobs.open_db("jobs_db")
    # checks how many jobs in db now
    num_db_jobs_after_save = len(list(db_cursor.execute("SELECT * FROM JOBS;")))

    job_name = jobs[1]['title']  # this is title of 1st job from github jobs API
    result = db_cursor.execute("SELECT * FROM JOBS WHERE title = ?;", (job_name,))
    num_results = len(list(result))
    GatherJobs.close_db(db_connection)  # close db connection
    # if the number of new jobs added is same as the difference between jobs now and jobs before in db then test passed
    assert num_jobs_from_api == num_db_jobs_after_save - num_db_jobs_before_save
    # if the results from this query is 1 or more, we know this job saved correctly to the db
    assert num_results >= 1
