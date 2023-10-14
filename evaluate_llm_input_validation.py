import boto3

s3_client = boto3.client('s3')


def handler(event, context):
    # TODO: may get it from some storage
    available_metrics = ["Sanity Check", "Accuracy Check", "Compact Check", "Relevancy Check", "Redundancy Check",
                         "Form Check", "Cosine Metric"]
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

    bucket, prefix = parse_s3_location(s3_location)
    s3_path = handle_s3_path(s3_client, bucket, prefix)
    result = [{"evaluation_metrics": evaluation_metrics, "model_family": event['evaluation_model_family'],
               "model_name": event['evaluation_model_name'], "evaluation_location": s3_location} for s3_location in
              s3_path]

    return {"result": result}


def parse_s3_location(location):
    """Parse s3 URL into bucket and prefix."""
    if not location.startswith("s3://"):
        raise ValueError("Invalid S3 URL")

    path_parts = location[5:].split("/", 1)  # strip off 's3://' and split by the first /
    bucket = path_parts[0]
    prefix = ""
    if len(path_parts) > 1:
        prefix = path_parts[1]
    return bucket, prefix


def handle_s3_path(s3_client, bucket, prefix):
    # Check if an object with the specified key exists
    if object_exists(s3_client, bucket, prefix):
        # It's an object, return object location
        return [f's3://{bucket}/{prefix}']
    else:
        # Assume it's a folder (even without a trailing slash), list objects inside
        objects_in_folder = list_objects(s3_client, bucket, prefix)
        if objects_in_folder:
            return objects_in_folder
        else:
            raise Exception("Invalid S3 Path")


def object_exists(s3_client, bucket, key):
    """Check if an object exists by trying to retrieve metadata about the object."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.ClientError as e:
        return False


def list_objects(s3_client, bucket, prefix):
    """List objects in folder"""
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix
    )

    objects = []
    if 'Contents' in response:
        for obj in response['Contents']:
            objects.append(f"s3://{bucket}/{obj['Key']}")

    return objects
