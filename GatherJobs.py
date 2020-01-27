import json
import requests
import time
# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn http

def main():
    jobs = []
    gitJobsURL = "https://jobs.github.com/positions.json?"
    pageNum = 0
    while pageNum < 5:
        pageNum = pageNum + 1
        parameters = {'page': pageNum}
        req = requests.get(url=gitJobsURL, params=parameters)
        data = req.json()

        jobs.append(data)
        time.sleep(.1)

    for page in jobs:
        print(page)




if __name__ == '__main__':
    main()
