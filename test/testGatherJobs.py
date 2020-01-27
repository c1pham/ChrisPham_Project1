import pytest
import GatherJobs

def test_Getting_jobs():
    jobs = []
    jobs = GatherJobs.getJobs(jobs)
    numJobs = len(jobs)

   assert numJobs > 99


def testWriteFile():
    main()
    jobFile = open("jobs.txt", 'r')

    linesInFile = jobFile.readlines()

