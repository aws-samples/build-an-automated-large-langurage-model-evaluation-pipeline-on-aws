import boto3
from handlers.utils.evaluation_util import EvaluationUtils

s3_client = boto3.client('s3')
evaluation_utils = EvaluationUtils("SolutionTableDDB")


def handler(event, context):
    available_metrics = evaluation_utils.get_fmeval_metric()
    evaluation_metrics = event.get("evaluation_metrics", [])

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
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")

    if not "instance_type" in event:
        raise Exception("instance_type is required")
    instance_type = event["instance_type"]

    return {"result": [{"metric": metric, "evaluation_location": s3_location, "instance_type": instance_type} for metric in evaluation_metrics]}


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

