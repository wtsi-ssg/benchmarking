#!/bin/env python

import argparse
import json

import boto3
from botocore.exceptions import ClientError
import jsonschema
import psycopg2
from amqp import Connection

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
                filename = record['s3']['object']['key']
                # Download new file from S3
                print(f'Downloading file {filename}')
                try:
                    res = client.get_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except boto3.S3.Client.exceptions.NoSuchKey:
                    next
                # Validate it against schema
                doc = json.load(res['Body'])
                res['Body'].close()
                try:
                    jsonschema.validate(instance = doc, schema=schema)
                    print(f'File {filename} has passed validation')
                    # It has passed? Send it to postgres database
                    # TODO: Catch exceptions from this and if it fails don't delete
                    curs.execute("insert into returned_results (jsondata) values (%s)", json.dumps(doc))
                except jsonschema.exceptions.ValidationError as err:
                    print(f'Downloaded file does not validate: {err.message}')
                    pass
                print(f'Deleting file {filename}')
                # Delete it from S3
                try:
                    res_del = client.delete_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except ClientError as ex:
                    pass
    pgconn.close()

parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
parser.add_argument('user', metavar='user', type=str, nargs='?',
                    help='rabbitmq username', default='guest')
parser.add_argument('password', metavar='password', type=str, nargs='?',
                    help='rabbitmq password', default='password')
parser.add_argument('dsn', metavar='dsn', type=str, nargs='?',
                    help='postgres host', default='dbname=benchmarking user=postgres password=postgres')

args = parser.parse_args()
DSN = args.dsn

with open('jsonschema.json', mode='r') as f:
    schema = json.load(f)

# Connect to Rabbit MQ server providing S3 notifications
conn = Connection(host=args.host, userid=args.user,
                  password=args.password, virtual_host="/")
conn.connect()

# Set up channel to recieve from queue
channel = conn.channel()
channel.basic_consume(queue='returned_results', callback=dump_message)
# Mainloop
while True:
    conn.drain_events()
