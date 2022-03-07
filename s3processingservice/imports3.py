#!/bin/env python

import argparse
import json

import boto3
import jsonschema
import psycopg2
from librabbitmq import Connection

DSN = "dbname=benchmarking user=postgres password=postgres"

def dump_message(message):
    # Connect to destination Postgres server
    pgconn = psycopg2.connect(DSN)

    with pgconn:
        with pgconn.cursor() as curs:
            # Open connection to S3
            client = boto3.client('s3', endpoint_url ='https://cog.sanger.ac.uk')
            # DEBUG: print("Body:'%s', Properties:'%s', DeliveryInfo:'%s'" % (
            # DEBUG: message.body, message.properties, message.delivery_info))

            # Read notification from queue
            bd = json.loads(message.body)
            for record in bd['Records']:
                # Check it is for us
                if record['eventName'] != 's3:ObjectCreated:Post' or record['s3']['bucket']['name'] != 'it_randd':
                    next

                # Download new file from S3
                try:
                    res = client.get_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except boto3.S3.Client.exceptions.NoSuchKey:
                    next
                # Validate it against schema
                doc = res['Body'].read()
                res['Body'].close()
                try:
                    jsonschema.validate(instance = doc, schema=schema)
                    # It has passed? Send it to postgres database
                    # TODO: Check return from this and if it fails don't delete
                    curs.execute("insert into mytable (jsondata) values (%s)", doc)
                except jsonschema.exceptions.ValidationError as err:
                    pass

                # Delete it from S3
                try:
                    res_del = client.delete_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except boto3.S3.Client.exceptions.NoSuchKey:
                    pass
            message.ack()
    pgconn.close()

# Read in ps
with open('benchmarkingdb.dsn', 'r') as f:
    DSN = f.read()
parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
args = parser.parse_args()

with open('jsonschema.json', mode='r') as f:
    schema = json.load(f.read())

# Connect to Rabbit MQ server providing S3 notifications
conn = Connection(host=args.host, userid="guest",
                  password="guest", virtual_host="/")

# Set up channel to recieve from queue
channel = conn.channel()
channel.basic_consume(queue='returned_results', callback=dump_message)
# Mainloop
while True:
    conn.drain_events()
