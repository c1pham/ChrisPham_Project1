import DataController
import JobCollector
import MapView


def main():
    job_db_connection, job_db_cursor = DataController.open_db("jobs_db")
    loc_db_connection, loc_db_cursor = DataController.open_db("location_db")
    DataController.create_jobs_table(job_db_cursor)
    DataController.create_location_cache_table(loc_db_cursor)
    github_jobs = JobCollector.get_github_jobs()
    stack_overflow_jobs = JobCollector.get_stack_overflow_jobs()

    processed_github_jobs = DataController.process_all_github_jobs(github_jobs)
    processed_stack_overflow_jobs = DataController.process_all_stack_overflow_jobs(stack_overflow_jobs)

    DataController.save_jobs_to_db(job_db_cursor, processed_github_jobs)
    DataController.save_jobs_to_db(job_db_cursor, processed_stack_overflow_jobs)

    jobs_from_db = DataController.load_jobs_from_db(job_db_cursor)
    non_remote_jobs = DataController.get_all_non_remote_jobs(jobs_from_db)
    jobs_data_frame = DataController.process_job_data_into_dataframe(loc_db_cursor, non_remote_jobs)

    MapView.make_jobs_map(jobs_data_frame)

    DataController.close_db(job_db_connection)
    DataController.close_db(loc_db_connection)


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
