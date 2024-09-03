from ragas.prepare_environment import prepare_environment
import sys
directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

from ragas.ragas_evaluation import KnowledgeBasesEvaluations

import json
import boto3
s3 = boto3.client('s3')
def download_jsonlines_from_s3(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    lines = obj['Body'].read().decode('utf-8').splitlines()
    return lines


def lambda_handler(event, context):
    bucket = event['evaluation_location'].split('/')[2]
    key = '/'.join(event['evaluation_location'].split('/')[3:])
    print(bucket, key)
    lines = download_jsonlines_from_s3(bucket, key)
    print(lines)

