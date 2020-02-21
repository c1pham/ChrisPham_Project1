import requests
import time
from typing import Tuple
from typing import List
from typing import Dict
import feedparser
import ssl

# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request


def main():
    get_stack_overflow_jobs()
    get_stack_overflow_jobs()


# get data from stack overflow rss feed
def get_stack_overflow_jobs():
    # monkey patch
    ssl._create_default_https_context = ssl._create_unverified_context
    raw_data = feedparser.parse('https://stackoverflow.com/jobs/feed')
    return raw_data.entries


# get github data from API
def get_github_jobs() -> List[Dict]:
    all_jobs = []
    # Link to API that retrieves job posting data
    git_jobs_url = "https://jobs.github.com/positions.json?"
    page_num = 1
    # retrieves about 5 pages, puts all jobs in the job list
    more_jobs = True
    error_code_responses = 0
    while more_jobs and error_code_responses < 10:  # after 10 errors will stop requesting
        parameters = {'page': page_num}  # param to get jobs from a specific page
        req = requests.get(url=git_jobs_url, params=parameters)  # get jobs
        if str(req) == "<Response [200]>":  # if message is 200, then convert to json and print
            jobs_from_api = req.json()
            all_jobs.extend(jobs_from_api)  # move jobs from api list to job list
            time.sleep(.1)
            page_num = page_num + 1  # if successful then increment page counter
            if len(jobs_from_api) < 50:  # if the length of the job page is less than 50 then it is last page
                more_jobs = False
        else:  # if the message is not 200 then it means request was not successful
            error_code_responses += 1
    return all_jobs


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
