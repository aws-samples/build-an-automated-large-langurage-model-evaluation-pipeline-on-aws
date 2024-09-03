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
question = "What are some of the ways to access JumpStart?"
ground_truth = "SageMaker JumpStart provides pretrained, open-source models for a wide range of problem types to help you get started with machine learning. You can incrementally train and tune these models before deployment. JumpStart also provides solution templates that set up infrastructure for common use cases, and executable example notebooks for machine learning with SageMaker. You can access the pretrained models, solution templates, and examples through the JumpStart landing page in Amazon SageMaker Studio. You can also access JumpStart models using the SageMaker Python SDK.|You can access JumpStart through the JumpStart landing page in Amazon SageMaker Studio. You can also access JumpStart models using the SageMaker Python SDK."

# variables
directory_to_extract_to = '/tmp'
path_to_zip_file = directory_to_extract_to + '/' + lib_file
dataset_json_file_name = "dataset.pickle"  # If this lambda is being called multiple times, this file will be updated. Consider to make it unique. Tried csv and json, both have some issue.

# Download dependencies
s3_client = boto3.client('s3')
s3_client.download_file(lib_bucket, lib_file, path_to_zip_file)

# Unzip dependencies
with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
    zip_ref.extractall(directory_to_extract_to)

# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

# import dependencies
from utils.evaluation import KnowledgeBasesEvaluations
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
    )

metrics = [
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision
]

MODEL_ID_EVAL = "anthropic.claude-3-sonnet-20240229-v1:0"
MODEL_ID_GEN = "anthropic.claude-3-haiku-20240307-v1:0"

def lambda_handler(event, context):
    questions = [question]
    ground_truths = [ground_truth]

    kb_evaluate = KnowledgeBasesEvaluations(model_id_eval=MODEL_ID_EVAL, 
        model_id_generation=MODEL_ID_GEN, 
        metrics=metrics,
        questions=questions, 
        ground_truth=ground_truths, 
        KB_ID=kb_id,
        )

    dataset = kb_evaluate.prepare_evaluation_dataset()

    
    with open(directory_to_extract_to + "/" + dataset_json_file_name, 'wb') as handle:
        pickle.dump(dataset, handle, protocol=pickle.HIGHEST_PROTOCOL)
    s3_client.upload_file(directory_to_extract_to + "/" + dataset_json_file_name, result_bucket, dataset_json_file_name)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
