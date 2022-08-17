#!/bin/env python

import argparse
import json

from amqp import Connection

parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
parser.add_argument('user', metavar='user', type=str, nargs='?',
                    help='rabbitmq username', default='guest')
parser.add_argument('password', metavar='password', type=str, nargs='?',
                    help='rabbitmq password', default='password')
parser.add_argument('filename', metavar='file', type=str, nargs='?',
                    help='postgres host', default='dbname=benchmarking user=postgres password=postgres')

args = parser.parse_args()

record = {
    "Records": [
        {
            "eventName":"s3:ObjectCreated:Post",
            "s3" : {
                "bucket" : {
                    "name":"it_randd"
                },
                "object": {
                    "key" : args.filename
                }
            }
        }
    ]
    }
print(json.dumps(record))

# Connect to Rabbit MQ server providing S3 notifications
conn = Connection(host=args.host, userid=args.user,
                  password=args.password, virtual_host="/")
conn.connect()

# Set up channel to send to queue
channel = conn.channel()
channel.basic_publish(routing_key='returned_results', msg=record)
