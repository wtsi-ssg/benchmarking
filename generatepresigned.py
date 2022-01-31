#!/bin/env python3

import boto3
import requests
import json

client = boto3.client('s3', endpoint_url ='https://it_randd.cog.sanger.ac.uk')

Fields = {"Content-Type":"application/json"}

res = client.generate_presigned_post('it_randd',
                                     'results/sample_result.json',
                                     Fields=Fields,
                                     Conditions=[{'Content-Type':'application/json'},
                                                 ["content-length-range", 1, 10485760],
                                                 ["starts-with", "$key", "results/"]])
print(res)
with open("demofile2.txt", "a") as f:
    f.write(json.dumps(res))

#with open('a.txt', 'rb') as f: 
#    files = {'file': ('a.txt', f)}
#    http_response = requests.post(res['url'], data=res['fields'], files=files)
#    print(http_response.content)

