import boto3
from handlers.utils.evaluation_util import EvaluationUtils

s3_client = boto3.client('s3')
evaluation_utils = EvaluationUtils("SolutionTableDDB")


def handler(event, context):
    available_metrics = evaluation_utils.get_all_metrics()
    evaluation_metrics = event.get("metrics", [])

    if "evaluation_model_family" not in event:
        raise Exception("no evaluation_model_family in event")

    if "evaluation_model_name" not in event:
        raise Exception("no evaluation_model_name in event")

    for metric in evaluation_metrics:
        if metric not in available_metrics:
            del evaluation_metrics[metric]

    if len(evaluation_metrics) == 0:
        evaluation_metrics = available_metrics

    # handle the s3 location
    if "evaluation_location" not in event:
        raise Exception("evaluation_location is required")

    s3_location = event["evaluation_location"]

    bucket, key = parse_s3_location(s3_location)
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")
    json_lines = parse_s3_jsonl_object(s3_client, bucket, key)
    result = [{"evaluation_metrics": evaluation_metrics, "model_family": event['evaluation_model_family'],
               "model_name": event['evaluation_model_name'], "evaluation_question_answer": eachline} for eachline in
              json_lines]

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

# given the bucket and key which is a jsonl file, return a list of jsonl content
def parse_s3_jsonl_object(s3_cleint, bucket_name, object_key):

    try:
        response = s3_cleint.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')

        # Split the content into lines and return as a list
        json_lines = content.split('\n')
        return json_lines

    except Exception as e:
        print(f"Error reading S3 object: {e}")
        return []

