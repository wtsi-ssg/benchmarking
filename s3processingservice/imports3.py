#!/bin/env python

import argparse
import json

import boto3
from botocore.exceptions import ClientError
import jsonschema
import psycopg2
import psycopg2.extras
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
                filename:str = record['s3']['object']['key']
                if record['eventName'] != 's3:ObjectCreated:Post' or record['s3']['bucket']['name'] != 'it_randd' or not (filename.startswith('results/') or filename.startswith('ci_results/')):
                    continue
                # Download new file from S3
                print(f'Downloading file {filename}')
                try:
                    res = client.get_object(Bucket='it-randd', Key=record['s3']['object']['key'])
                except ClientError as ex:
                    if ex.response['Error']['Code'] == 'NoSuchKey':
                        print(f'No object found {filename} - skipping')
                        continue
                    else:
                        raise
                # Validate it against schema
                doc = res['Body'].read()
                docconv = json.loads(doc)
                res['Body'].close()
                if filename.startswith('results/'):
                    try:
                        jsonschema.validate(instance = docconv, schema=system_results_schema)
                        print(f'File {filename} has passed validation')
                        # It has passed? Send it to postgres database
                        # TODO: Catch exceptions from this and if it fails don't delete
                        curs.execute("INSERT INTO returned_results (jsondata) VALUES (%s)", (psycopg2.extras.Json(docconv),))
                        # Update any potentially affected materialised views
                        curs.execute("REFRESH MATERIALIZED VIEW cpu_corecount WITH DATA")
                        curs.execute("REFRESH MATERIALIZED VIEW cpu_results WITH DATA")
                        curs.execute("REFRESH MATERIALIZED VIEW geekbench5_detailed_results WITH DATA")
                        curs.execute("REFRESH MATERIALIZED VIEW geekbench5_results WITH DATA")
                        curs.execute("REFRESH MATERIALIZED VIEW iozone_results WITH DATA")
                        curs.execute("REFRESH MATERIALIZED VIEW mbw_results WITH DATA")
                    except jsonschema.exceptions.ValidationError as err:
                        print(f'Downloaded file does not validate: {err.message}')
                        pass
                elif filename.startswith('ci_results/'):
                    try:
                        jsonschema.validate(instance = docconv, schema=ci_results_schema)
                        print(f'File {filename} has passed validation')
                        # It has passed? Send it to postgres database
                        # TODO: Catch exceptions from this and if it fails don't delete
                        curs.execute("INSERT INTO ci_returned_results (jsondata) VALUES (%s)", (psycopg2.extras.Json(docconv),))
                        # Update any potentially affected materialised views
                        curs.execute("REFRESH MATERIALIZED VIEW ci_cpu_results WITH DATA")
                     except jsonschema.exceptions.ValidationError as err:
                        print(f'Downloaded file does not validate: {err.message}')
                        pass
                if args.delete:
                    print(f'Deleting file {filename}')
                    # Delete it from S3
                    try:
                        res_del = client.delete_object(Bucket='it-randd', Key=record['s3']['object']['key'])
                    except ClientError as ex:
                        pass
    pgconn.close()
    channel.basic_ack(message.delivery_tag)


parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
parser.add_argument('vhost', metavar='vhost', type=str, nargs='?',
                    help='rabbitmq vhost', default='/')
parser.add_argument('user', metavar='user', type=str, nargs='?',
                    help='rabbitmq username', default='guest')
parser.add_argument('password', metavar='password', type=str, nargs='?',
                    help='rabbitmq password', default='password')
parser.add_argument('dsn', metavar='dsn', type=str, nargs='?',
                    help='postgres host', default='dbname=benchmarking user=postgres password=postgres')
parser.add_argument('delete', metavar='delete', type=bool, nargs='?',
                    help='Delete notified files', default=True)

args = parser.parse_args()
DSN = args.dsn

with open('system_results.json', mode='r') as f:
    system_results_schema = json.load(f)
with open('ci_results.json', mode='r') as f:
    ci_results_schema = json.load(f)

# Connect to Rabbit MQ server providing S3 notifications
conn = Connection(host=args.host, userid=args.user,
                  password=args.password, virtual_host=args.vhost)
conn.connect()

# Set up channel to recieve from queue
channel = conn.channel()
channel.basic_consume(queue='returned_results', callback=dump_message)
# Mainloop
while True:
    conn.drain_events()
