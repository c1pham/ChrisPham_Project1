import json
import requests
import time
# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn http
# https://realpython.com/python-json/
# this is for learning JSON


def main():
    jobs = []
    jobs = getJobs(jobs)
    print(len(jobs))
    fileName = "jobs.txt"
    writeJobsToFile(jobs, fileName)

    readFromFile()


def getJobs(jobsList):
    gitJobsURL = "https://jobs.github.com/positions.json?"
    pageNum = 0
    while pageNum < 5:
        pageNum = pageNum + 1
        parameters = {'page': pageNum}
        req = requests.get(url=gitJobsURL, params=parameters)
        data = req.json()
        transferObjToList(data, jobsList)
        time.sleep(1)
    return jobsList


def writeJobsToFile(jobsList, fileName):
    writing_file = open(fileName, 'w')
    for page in jobsList:
        #print(page)
        print(page, file=writing_file)
    writing_file.close()


def transferObjToList(jsonList, receiveList):
    for entry in jsonList:
        receiveList.append(entry)


if __name__ == '__main__':
    main()
