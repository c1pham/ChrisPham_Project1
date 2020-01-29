import requests
import time
# https://www.geeksforgeeks.org/get-post-requests-using-python/
# this is page I used for reference to learn request


def main():
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
        jobs_from_api = req.json()
        transfer_obj_to_list(jobs_from_api, jobs_list)
        time.sleep(.1)
    return jobs_list


def write_jobs_to_file(jobs_list, file_name):  # write dictionary objects into file
    writing_file = open(file_name, 'w')
    for entry in jobs_list:
        print(entry, file=writing_file)
    writing_file.close()


# move list from API to python job list
def transfer_obj_to_list(json_list, receive_list):
    for entry in json_list:
        receive_list.append(entry)


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
