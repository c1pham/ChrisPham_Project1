import pytest
import GatherJobs

def test_Getting_jobs():
    jobs = []
    jobs = GatherJobs.getJobs(jobs)
    numJobs = len(jobs)
    # checks to see if it gathered the right amount of jobs
    assert numJobs > 100


def testWriteFile():
    GatherJobs.main()
    jobFile = open("jobs.txt", 'r')
    linesInFile = jobFile.readlines()
    count = 0
    # this looks through the document to find an line that has a job title that I know should be there
    for line in linesInFile:
        indicator = line.find("(Senior-) Full Stack TypeScript Developer (m/w/d)")
        if indicator != -1:
            count = count + 1
    assert count != 0

