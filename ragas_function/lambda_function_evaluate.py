import boto3
import json
import sys
import zipfile
import pickle
import os

# We need to provide the following values. Better use env var. Hard coded for testing purpose.
lib_bucket = os.environ.get('LIB_BUCKET')       # bucket name created in create_bucket.py
lib_file = os.environ.get('LIB_FILE')       # zip file name created in create_bucket.py
kb_id = os.environ.get('KB_ID')             # Knowledge Base ID created in create_kb.py
result_bucket = os.environ.get("RESULT_BUCKET")

# variables
question = None
ground_truth = None
directory_to_extract_to = '/tmp'
path_to_zip_file = directory_to_extract_to + '/' + lib_file
dataset_json_file_name = "dataset.pickle"  # If this lambda is being called multiple times, this file will be updated. Consider to make it unique. Tried csv and json, both have some issue.
results_json_file_name = "results.csv"     # Also consider to make this one unique.

# Download dependencies
s3_client = boto3.client('s3')
s3_client.download_file(lib_bucket, lib_file, path_to_zip_file)
#
# # Unzip dependencies
# with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
#     zip_ref.extractall(directory_to_extract_to)
#
# # update path, so that dependencies can be found
# sys.path.insert(0, directory_to_extract_to)

# import dependencies
# from utils.evaluation import KnowledgeBasesEvaluations
# from ragas.metrics import (
#     faithfulness,
#     answer_relevancy,
#     context_precision,
#     context_recall
#     )

# metrics = [
#     faithfulness,
#     answer_relevancy,
#     context_recall,
#     context_precision
# ]

MODEL_ID_EVAL = "anthropic.claude-3-sonnet-20240229-v1:0"
MODEL_ID_GEN = "anthropic.claude-3-haiku-20240307-v1:0"


def parse_s3_jsonl_object(s3_cleint, bucket_name, object_key):

    try:
        response = s3_cleint.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')
        # Split the content into lines and return as a list
        json_lines = content.strip().split('\n')
        return json_lines

    except Exception as e:
        print(f"Error reading S3 object: {e}")
        return []


def lambda_handler(event, context):
    s3_location = event['evaluation_location']
    bucket, key = parse_s3_location(s3_location)
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")
    json_lines = parse_s3_jsonl_object(s3_client, bucket, key)
    questions = []
    contexts = []
    answers = []
    ground_truths = []

    for line in json_lines:
        # Parse the JSON from the current line
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Problematic line: {line}")
            continue

        # Append the id and question to their respective lists
        questions.append(data['QUESTION'])
        contexts.append(data['CONTEXT'])
        answers.append(data['RESPONSE'])
        ground_truths.append(data['EXPECTEDANSWER'])

    result = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
    }
    print(result)
    return result
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
        # replace " with ' in content
        content = content.replace('"', "'")
        # Split the content into lines and return as a list
        json_lines = content.split('\n')
        return json_lines

    except Exception as e:
        print(f"Error reading S3 object: {e}")
        return []
