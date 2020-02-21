import DataController
import JobCollector


def main():  # collect jobs from github jobs API and store into text file
    db_connection, db_cursor = DataController.open_db("jobs_db")
    DataController.create_jobs_table(db_cursor)
    github_jobs = JobCollector.get_github_jobs()
    stack_overflow_jobs = JobCollector.get_stack_overflow_jobs()

    processed_github_jobs = DataController.process_all_github_jobs(github_jobs)
    processed_stack_overflow_jobs = DataController.process_all_stack_overflow_jobs(stack_overflow_jobs)

    DataController.save_jobs_to_db(db_cursor, processed_github_jobs)
    DataController.save_jobs_to_db(db_cursor, processed_stack_overflow_jobs)

    DataController.close_db(db_connection)


if __name__ == '__main__':  # if running from this file, then run the main function
    main()
