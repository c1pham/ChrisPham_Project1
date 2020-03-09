# ChrisPham_Project1 My name is Christopher Pham. You need to install pytest, feedparser, typing, requests, geopy, pandas, plotly, dash, datetime, and bs4 library
# You also need python 3.7. The file that needs to be run is app.py
# The project takes jobs from github jobs API and stack overflow rss feed, and saves it into a database. 
# This job data is then taken and shown on a webpage. The user can see all the remote jobs by pressing a remote jobs button.
# The user can see the job info on the map by hovering over the points. However if there are more than 20 jobs in a location.
# If they press on a point they see more information about the job.
# The user can filter out the jobs by title, technology, company, and time. 
# The technology filter allows the user to specify 3 technologies and a job will if any of the three technologies show up in the job title description or tags
# It also has 19 test cases to test the application
# The test see if the job data from both sources are downloaded correctly, saved correctly, and reject bad data. We also check if the database and job table is created correctly
# The title, technology, time, and title filters are also all tested for good data and bad data
# The selected job info from the plotly map is also tested
# The project has all parts completed