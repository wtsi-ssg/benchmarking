#!/bin/env python3

import boto3
import json

client = boto3.client('s3', endpoint_url ='https://cog.sanger.ac.uk')

Fields = {"Content-Type":"application/json", "acl":"private"}

def create_upload_presigned(prefix:str, filename:str):
    res = client.generate_presigned_post('it_randd',
                                        f"{prefix}" + '/${filename}',
                                        Fields=Fields,
                                        Conditions=[{'acl':'private'},
                                                    {'Content-Type':'application/json'},
                                                    ["content-length-range", 1, 10485760],
                                                    ["starts-with", "$key", f"{prefix}/"]],
                                        ExpiresIn=604800)
    print(res)
    with open(filename, "a") as f:
        f.write(json.dumps(res))

    #does equiv of:
    #  s3cmd put post_signed_url.json s3://it-randd/post_signed_url.json
    #  s3cmd setacl s3://it-randd/post_signed_url.json --acl-public

    response = client.put_object(ACL='public-read',
                                Body=json.dumps(res),
                                Bucket='it-randd',
                                ContentType='application/json',
                                Key=filename)


# Create returned_results URL for system benchmarking
create_upload_presigned('results', 'post_signed_url.json')
# Create returned results URL for CI mode
create_upload_presigned('ci_results', 'post_signed_url_ci.json')
