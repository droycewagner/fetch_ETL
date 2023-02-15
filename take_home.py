"""
System and Python dependencies, as well as instructions for running this script are given in the readme at the GitHub page: 

https://github.com/droycewagner/fetch_ETL

This Python script runs an existing local SQS server (given as a docker -- see the Dependencies section of the Readme), and for each response from the server: 
* checks that the response is properly formatted, 
* masks the PII 'ip' and 'device_id' using a hash, 
* writes the masked data to a PostgreSQL server. 
"""


import boto3 # for the local AWS server
import psycopg2 as psy # for postgresql
import hashlib # we will mask PII using a hash
import json

def my_hash(str):
    """
    Given a string str, hash with sha256. 
    """
    return hashlib.sha256(str.encode('utf-8')).hexdigest()

def hash_entry(entry):
    """
    Given a dictionary, hash the values corresponding to 'ip' and 'device_id', 
    assuming that these exist. 
    """
    e=entry.copy()
    e['masked_ip']=my_hash(e['ip'])
    e['masked_device_id']=my_hash(e['device_id'])
    del e['ip']
    del e['device_id']
    e['app_version']='1'
    return e

# get a resource representing the SQS server
endpoint_url = "http://localhost.localstack.cloud:4566"
sqs = boto3.client('sqs', endpoint_url=endpoint_url)
sqs.list_queues()
queue_url='http://localhost:4566/000000000000/login-queue'

# connect to the PostgreSQL server
conn = psy.connect("dbname='postgres' user='postgres' password='postgres' host='localhost' port='5432'")
cur = conn.cursor()
cur.execute("SELECT * FROM user_logins LIMIT 0")
colnames = [desc[0] for desc in cur.description]

# loop through responses from the SQS server
while True: 
    
    # get response from server
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    
    # format response as json
    message = response['Messages'][0]
    entry=json.loads(message['Body'])
    
    # break if the response is invalid
    if len(list(entry.keys())) != 6: 
        print(entry.keys())
        break
    
    # hash the PPI
    masked_entry=hash_entry(entry)
    
    # write masked data to the PostgreSQL server
    query_sql = """ insert into user_logins select * from json_populate_record(NULL::user_logins, %s) """
    cur.execute(query_sql, (json.dumps(masked_entry),))
    conn.commit()
    
    # Delete received message
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )

# close the PostgreSQL connection
conn.close()