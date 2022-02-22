#!/bin/env python3

import boto3
import json

client = boto3.client('s3', endpoint_url ='https://cog.sanger.ac.uk')

Fields = {"Content-Type":"application/json", "acl":"private"}

res = client.generate_presigned_post('it_randd',
                                     'results/${filename}',
                                     Fields=Fields,
                                     Conditions=[{'acl':'private'},
                                                 {'Content-Type':'application/json'},
                                                 ["content-length-range", 1, 10485760],
                                                 ["starts-with", "$key", "results/"]])
print(res)
with open("post_signed_url.json", "a") as f:
    f.write(json.dumps(res))

#does equiv of:
#  s3cmd put post_signed_url.json s3://it_randd/post_signed_url.json
#  s3cmd setacl s3://it_randd/post_signed_url.json --acl-public

response = client.put_object(ACL='public-read',
                             Body=json.dumps(res),
                             Bucket='it_randd',
                             ContentType='application/json',
                             Key='post_signed_url.json')
