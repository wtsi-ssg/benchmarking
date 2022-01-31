#!/bin/env python3

import boto3
import requests
import json

client = boto3.client('s3', endpoint_url ='https://cog.sanger.ac.uk')

Fields = {"Content-Type":"application/json"}

res = client.generate_presigned_post('it_randd',
                                     'results/${filename}',
                                     Fields=Fields,
                                     Conditions=[{'Content-Type':'application/json'},
                                                 ["content-length-range", 1, 10485760],
                                                 ["starts-with", "$key", "results/"]])
print(res)
with open("post_signed_url.json", "a") as f:
    f.write(json.dumps(res))

response = client.put_object(ACL='public-read',
                             Body=json.dumps(res),
                             Bucket='it_randd',
                             ContentType='application/json',
                             Key='post_signed_url.json')
#TODO: s3cmd put post_signed_url.json s3://it_randd/post_signed_url.json
#TODO: s3cmd setacl s3://it_randd/post_signed_url.json --acl-public

#with open('a.txt', 'rb') as f: 
#    files = {'file': ('a.txt', f)}
#    http_response = requests.post(res['url'], data=res['fields'], files=files)
#    print(http_response.content)

