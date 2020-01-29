import pytest
import GatherJobs


def test_getting_jobs():
    jobs = []
    jobs = GatherJobs.get_jobs(jobs)
    num_jobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert num_jobs > 100


def test_write_file():
    GatherJobs.main()
    job_file = open("jobs.txt", 'r')
    lines_in_file = job_file.readlines()
    count = 0
    # this looks through the document to find an line that has a job title that I know should be there
    for line in lines_in_file:
        indicator = line.find("(Senior-) Full Stack TypeScript Developer (m/w/d)")
        if indicator != -1:
            count = count + 1
    assert count != 0

