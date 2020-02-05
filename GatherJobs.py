import requests
import time


# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request


def main():  # collect jobs from github jobs API and store into text file
    jobs = []  # hold jobs
    jobs = get_jobs(jobs)
    file_name = "jobs.txt"
    write_jobs_to_file(jobs, file_name)


def get_jobs(jobs_list):
    # Link to API that retrieves job posting data
    git_jobs_url = "https://jobs.github.com/positions.json?"
    page_num = 1
    # retrieves about 5 pages, puts all jobs in the job list
    # you are making a *big* assumption that you won't need more than 5
    while page_num <= 5:
        page_num = page_num + 1
        parameters = {'page': page_num}  # param to get jobs from a specific page
        req = requests.get(url=git_jobs_url, params=parameters)  # get jobs
        if str(req) != "<Response [503]>":  # if message is not 503, then convert to json and print
            jobs_from_api = req.json()
            jobs_list.extend(jobs_from_api)  # move jobs from api list to job list
            time.sleep(.1)
    return jobs_list


def write_jobs_to_file(jobs_list, file_name):  # write dictionary objects into file
    writing_file = open(file_name, 'w')
    # json.dump(jobs_list, writing_file)
    print(jobs_list, file=writing_file)
    writing_file.close()


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
