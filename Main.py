import DataController
import JobCollector
import MapView


def main():
    # open db connections
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    # create tables
    DataController.create_jobs_table(job_db_cursor)
    DataController.create_location_cache_table(loc_db_cursor)

    github_jobs = JobCollector.get_github_jobs()
    stack_overflow_jobs = JobCollector.get_stack_overflow_jobs()
    # take job info and make it into dictionary the program can use
    processed_github_jobs = DataController.process_all_github_jobs(github_jobs)
    processed_stack_overflow_jobs = DataController.process_all_stack_overflow_jobs(stack_overflow_jobs)

    all_jobs = processed_github_jobs + processed_stack_overflow_jobs
    DataController.save_jobs_to_db(job_db_cursor, all_jobs)

    # save the jobs by committing to db
    DataController.close_db(job_db_connection)
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")

    # get all jobs from db
    jobs_from_db = DataController.load_jobs_from_db(job_db_cursor)
    non_remote_jobs = DataController.get_all_non_remote_jobs(jobs_from_db)
    jobs_data_frame, remote_or_unknown_jobs = DataController.process_job_data_into_data_frame(
        loc_db_cursor, non_remote_jobs)
    print(remote_or_unknown_jobs)
    figure = MapView.make_jobs_map(jobs_data_frame)
    # save jobs and location cache by committing to db
    DataController.close_db(job_db_connection)
    DataController.close_db(loc_db_connection)
    return figure


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
