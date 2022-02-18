#!/bin/env python

import argparse
import json

import boto3
import jsonschema
import psycopg2
from librabbitmq import Connection

DSN = "dbname=suppliers user=postgres password=postgres"

def dump_message(message):
    pgconn = psycopg2.connect(DSN)

    with conn:
        with conn.cursor() as curs:
            client = boto3.client('s3', endpoint_url ='https://cog.sanger.ac.uk')
            print("Body:'%s', Properties:'%s', DeliveryInfo:'%s'" % (
            message.body, message.properties, message.delivery_info))
            bd = json.loads(message.body)
            for record in bd['Records']:
                if record['eventName'] != 's3:ObjectCreated:Post' or record['s3']['bucket']['name'] != 'it_randd':
                    next

                # Get new file from S3
                try:
                    res = client.get_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except boto3.S3.Client.exceptions.NoSuchKey:
                    next
                # Validate it against schema
                doc = res['Body'].read()
                try:
                    jsonschema.validate(instance = doc, schema=schema)
                except jsonschema.exceptions.ValidationError as err:
                    pass
                res['Body'].close()
                # Send it to postgres database
                curs.execute("insert into mytable (jsondata) values (%s)", doc)

                # Delete it from S3
                try:
                    res_del = client.delete_object(Bucket='it_randd', Key=record['s3']['object']['key'])
                except boto3.S3.Client.exceptions.NoSuchKey:
                    pass
            message.ack()
    pgconn.close()


parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
args = parser.parse_args()

with open('jsonschema.json', mode='r') as f:
    schema = json.load(f.read())

conn = Connection(host=args.host, userid="guest",
                  password="guest", virtual_host="/")

channel = conn.channel()
channel.basic_consume(queue='returned_results', callback=dump_message)
while True:
    conn.drain_events()
