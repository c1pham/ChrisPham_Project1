import GatherJobs


def test_getting_jobs():
    jobs = []
    jobs = GatherJobs.get_jobs(jobs)  # get jobs from API
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


def test_write_file():
    GatherJobs.main()
    job_file = open("jobs.txt", 'r')
    lines_in_file = job_file.readlines()
    count = 0
    # this looks through the first line of document to find this job title because dump put all data in first line
    # find will return -1 if the string is not in there
    indicator = lines_in_file[0].find("(Senior-) Full Stack TypeScript Developer (m/w/d)")
    # if the find function returns anything else than -1, meaning it return position of string then the test passed
    assert indicator != 1

    # for line in lines_in_file:
    #    indicator = line.find("(Senior-) Full Stack TypeScript Developer (m/w/d)")
    #    if indicator != -1:
    #        count = count + 1
    # assert count != 0
