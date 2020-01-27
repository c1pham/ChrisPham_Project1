import requests
import time
# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request


def main():
    jobs = []  # hold jobs
    jobs = getJobs(jobs)
    fileName = "jobs.txt"
    writeJobsToFile(jobs, fileName)


def getJobs(jobsList):
    # Link to API that retreives job posting data
    gitJobsURL = "https://jobs.github.com/positions.json?"
    pageNum = 0
    # retreives about 5 pages, puts all jobs in the job list
    while pageNum < 5:
        pageNum = pageNum + 1
        parameters = {'page': pageNum}  # param to get jobs from a specific page
        req = requests.get(url=gitJobsURL, params=parameters)  # get jobs
        jobsFromAPI = req.json()
        transferObjToList(jobsFromAPI, jobsList)
        time.sleep(.1)
    return jobsList


def writeJobsToFile(jobsList, fileName):
    writing_file = open(fileName, 'w')
    for entry in jobsList:
        print(entry, file=writing_file)
    writing_file.close()


# move list from API to python job list
def transferObjToList(jsonList, receiveList):
    for entry in jsonList:
        receiveList.append(entry)


if __name__ == '__main__': # if running from this file, then run the main function
    main()
