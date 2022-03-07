import boto3

client = boto3.client('sns', endpoint_url ='https://cog.sanger.ac.uk')

response = client.create_topic( Name='returned_results',
    Attributes={
        'DisplayName ': 'Notify of returned benchmarking results'
    },
    Tags=[
        {
            'Key': 'string',
            'Value': 'string'
        },
    ]
)
