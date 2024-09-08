import boto3
from handlers.utils.evaluation_util import EvaluationUtils
import json
import pickle

s3_client = boto3.client('s3')
evaluation_utils = EvaluationUtils("SolutionTableDDB")


def read_jsonl_generator(file_path):
    with open(file_path, 'r') as jsonl_file:
        for line in jsonl_file:
            yield json.loads(line.strip())


def lambda_handler(event, context):
    print(event)
    available_metrics = [
        "faithfulness",
        "context_precision",
        "context_recall"
    ]
    evaluation_metrics = event.get("evaluation_metrics", [])

    if "evaluation_model_name" not in event:
        raise Exception("no evaluation_model_name in event")

    for metric in evaluation_metrics:
        if metric not in available_metrics:
            evaluation_metrics.remove(metric)

    if len(evaluation_metrics) == 0:
        evaluation_metrics = available_metrics

    # handle the s3 location
    if "evaluation_location" not in event:
        raise Exception("evaluation_location is required")

    s3_location = event["evaluation_location"]

    bucket, key = parse_s3_location(s3_location)
    key_path = '/'.join(key.split('/')[:-1])
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")

    # download the jsonl file from s3 and split them into pickle files
    s3_client.download_file(bucket, key, '/tmp/input.jsonl')
    pickle_list = []
    index = 0
    for item in read_jsonl_generator('/tmp/input.jsonl'):
        # Process each item (dictionary) here
        data = {
            "question": item["QUESTION"],
            "answer": item['ExpectedAnswer'],
            "contexts": item['CONTEXT'],
            "ground_truth": item['Response']
        }
        print(data)
        file = f'/tmp/ragas_{index}.pkl'
        target_key = f'{key_path}/ragas_{index}.pkl'

        with open(file, 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
            s3_client.upload_file(file, bucket, target_key)
        pickle_list.append(f"s3://{bucket}/{target_key}")

        index += 1

    result = [{"evaluation_metrics": evaluation_metrics,
               "model_name": event['evaluation_model_name'],
               "evaluation_location": eachline} for eachline in pickle_list]
    print(result)
    return {"result": result}


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

