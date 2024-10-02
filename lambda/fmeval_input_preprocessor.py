import boto3
import json
from handlers.utils.evaluation_util import EvaluationUtils

s3_client = boto3.client('s3')
evaluation_utils = EvaluationUtils("SolutionTableDDB")

def read_jsonl_generator(file_path):
    with open(file_path, 'r') as jsonl_file:
        for line in jsonl_file:
            yield json.loads(line.strip())

def handler(event, context):
    available_metrics = evaluation_utils.get_fmeval_metric()

    evaluation_metrics = event.get("evaluation_metrics", [])

    metrics = [metric for metric in evaluation_metrics if metric in available_metrics]


    # handle the s3 location
    if "evaluation_location" not in event:
        raise Exception("evaluation_location is required")

    s3_location = event["evaluation_location"]


    bucket, key = parse_s3_location(s3_location)
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")

    if not "instance_type" in event:
        raise Exception("instance_type is required")
    instance_type = event["instance_type"]

    # download the file and convert the format
    s3_client.download_file(bucket, key, '/tmp/input.jsonl')
    updated_items = []
    for item in read_jsonl_generator('/tmp/input.jsonl'):
        context = item["CONTEXT"]

        context_string = ". ".join([item[0] for item in context])
        updated_item = {'id': item['id'][0],
                        'QUESTION': item['QUESTION'][0],
                        'CONTEXT': context_string,
                        'ExpectedAnswer': item['ExpectedAnswer'][0],
                        'Response': item['Response'][0]}
        updated_items.append(updated_item)

    with open('/tmp/result_updated.jsonl', 'w') as jsonl_file:
        for item in updated_items:
            jsonl_file.write(json.dumps(item) + '\n')

    key = key.replace(".jsonl", "_updated.jsonl")
    s3_client.upload_file('/tmp/result_updated.jsonl', bucket, key)
    return {"result": [{"metric": metric,
                        "evaluation_location": f"s3://{bucket}/{key}",
                        "instance_type": instance_type} for metric in metrics]}


def parse_s3_location(location):
    """Parse s3 URL into bucket and prefix."""
    print(location)
    if not location.startswith("s3://"):
        raise ValueError("Invalid S3 URL")

    path_parts = location[5:].split("/", 1)  # strip off 's3://' and split by the first /
    bucket = path_parts[0]

    if len(path_parts) == 1:
        raise Exception("Invalid S3 URL")
    prefix = path_parts[1]

    if not prefix.endswith(".jsonl"):
        raise Exception("Invalid S3 URL")


    return bucket, prefix


def object_exists(s3_client, bucket, key):
    """Check if an object exists by trying to retrieve metadata about the object."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.ClientError as e:
        return False