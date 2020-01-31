import requests
import time
import json


# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request
# https://developer.rhino3d.com/guides/rhinopython/python-xml-json/
# this page help me to learn json


def main():  # collect jobs from github jobs API and store into text file
    jobs = []  # hold jobs
    jobs = get_jobs(jobs)
    file_name = "jobs.txt"
    write_jobs_to_file(jobs, file_name)


def get_jobs(jobs_list):
    # Link to API that retrieves job posting data
    git_jobs_url = "https://jobs.github.com/positions.json?"
    page_num = 0
    # retrieves about 5 pages, puts all jobs in the job list
    while page_num < 5:
        page_num = page_num + 1
        parameters = {'page': page_num}  # param to get jobs from a specific page
        req = requests.get(url=git_jobs_url, params=parameters)  # get jobs
        if str(req) != "<Response [503]>":  # if message is not 503, then convert to json and print
            jobs_from_api = req.json()
            transfer_obj_to_list(jobs_from_api, jobs_list)
            time.sleep(.1)
    return jobs_list


def write_jobs_to_file(jobs_list, file_name):  # write dictionary objects into file
    writing_file = open(file_name, 'w')
    json.dump(jobs_list, writing_file)
    writing_file.close()


# move job from API list to programs own job list
def transfer_obj_to_list(json_list, receive_list):
    # for entry in json_list:
    #     receive_list.append(entry)
    receive_list.extend(json_list)


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
