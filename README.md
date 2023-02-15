# fetch_ETL

Extract, Transform, Load off an SQS Queue
=========================================

This project is a coding assessment for Fetch Rewards. It consists of a configuration file *docker-compose.yml* and a Python script *take_home.py*. The Python script runs an existing local SQS server (given as a docker -- see the Dependencies section of this Readme), and for each response from the server: 
* checks that the response is properly formatted, 
* masks the PII 'ip' and 'device_id' using a hash, 
* writes the masked data to a PostgreSQL server. 


Dependencies
------------

To run successfully on Ubuntu 20.04, the following dependencies are required:
* [docker and docker-compose](https://docs.docker.com/get-docker/)
* libpq-dev (`sudo apt-get install libpq-dev` should work on Ubuntu)
* [Python](https://www.python.org/downloads/)
* Install needed Python packages using: `pip install awscli-local localstack boto3 psycopg2`
* [psql](https://www.postgresql.org/download/)

The following dockers, which correspond to the SQS and PostgreSQL databases, should also be installed: 
* [Localstack docker](https://hub.docker.com/r/fetchdocker/data-takehome-localstack)
* [Postgres docker](https://hub.docker.com/r/fetchdocker/data-takehome-postgres)


Running the script
------------------

To run the project, open bash in a directory containing both the Python script and .yml file. From there: 

If necessary, configure aws: 

    configure aws

Run the database servers: 

    sudo service postgresql stop
    docker-compose up -d

Optionally confirm that the SQS server is running: 

    awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue`

Run the script: 

    python take_home.py

To confirm that entries are properly exported, connect to the Postgres database via

    psql -d postgres -U postgres -p 5432 -h localhost -W

and enter at the prompt: 

    postgres =# SELECT * FROM user_logins;


Further work
------------

A more complete ETL script would need the following improvements: 

* Handling server errors and error catching, especially in guaranteeing that any message from the SQS server has the appropriate fields. 
* Use of Python's type support. 
* Depending on the exact application, a more secure masking of PII data may be warranted; the hash could be customized in some way to hinder some sort of brute force lookup, or another method could be used entirely. 
* Correct output of version numbers (see the function `hash_entry` in `take_home.py`).

**Other questions:**

1. How can this application scale with a growing dataset?

Because the PII are merely hashed, this application runs in linear time on the number of SQS messages. There are no scalability concerns in that regard. 

2. How can PII be recovered later on?

Hash values of the PII could be stored server-side for later lookup. 

3. What assumptions were made? 

This script assumes that SQS messages are formatted with the correct fields and it does not make provision for other hanging behaviors or non-responsiveness of the servers. 