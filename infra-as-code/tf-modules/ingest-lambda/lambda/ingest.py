import json


def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print(f"New object created: s3://{bucket}/{key}")
        # Processing logic goes here...

    return {"statusCode": 200}
