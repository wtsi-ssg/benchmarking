#!/bin/env python

# Manually create dummy s3 message
# e.g. python create_test.py 192.168.3.1 user MxRwazxoAhn55aicDK9T7SPU6YAOhosqLK60SYxAPBM= 2022-11-09-175119_single_process_ranging.json

import argparse
import json
import amqp
from amqp import Connection

parser = argparse.ArgumentParser(description='Check queue for files to download from S3.')
parser.add_argument('host', metavar='host', type=str, nargs='?',
                    help='rabbitmq host', default='localhost')
parser.add_argument('vhost', metavar='vhost', type=str, nargs='?',
                    help='rabbitmq vhost', default='/')
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
                  password=args.password, virtual_host=args.vhost)
conn.connect()

# Set up channel to send to queue
channel = conn.channel()
message = amqp.basic_message.Message(body=json.dumps(record))
channel.basic_publish(routing_key='returned_results', msg=message)
