from ragasutils.prepare_environment import prepare_environment
import sys

import pandas as pd
import numpy as np

directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

from prompts.store import TemplateStore
from handlers.utils.evaluation_util import EvaluationUtils
from llm_api.invoke_llm import generate_result

import boto3

import os
import logging
import pickle

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import awswrangler as wr
import time

available_metrics = [
        "Cosine Metric",
        "Accuracy Check",
        "Compact Check",
        "Form Check",
        "Redundancy Check",
        "Relevancy Check",
        "Sanity Check",
    ]

s3 = boto3.client('s3')
bucket_name = os.getenv("ResultBucket")
database_name = os.getenv("ResultDatabase")

bedrock_client = boto3.client(service_name='bedrock-runtime')

def handler(event, context):
    logger.info(f"receiving event {event}")

    execution_id = event['execution_id'].split(":")[-1]
    bucket = event['input']['evaluation_location'].split('/')[2]
    key = '/'.join(event['input']['evaluation_location'].split('/')[3:])
    model_family = event['input']['model_family']
    model_name = event['input']['model_name']
    metrics = event['input']['evaluation_metrics']


    path = f"s3://{bucket_name}/llmeval_result/"

    # download the pickle file from s3
    s3.download_file(bucket, key, "/tmp/result.pickle")

    with open("/tmp/result.pickle", 'rb') as handle:
        dataset = pickle.load(handle)

    eval_data = []

    evaluation_utils = EvaluationUtils("SolutionTableDDB")

    simple_metrics = evaluation_utils.get_metric_names_by_type("Simple")
    # composed_metrics = evaluation_utils.get_metric_names_by_type("Composed")
    # similarity_metrics = evaluation_utils.get_metric_names_by_type("Similarity")

    logger.info("adding simple metrics")

    msg = evaluation_utils.get_evaluation_template()

    param_values = {
        "CONTEXT": ".".join(dataset['contexts'][0]),
        "INQUIRY": dataset['question'][0],
        "RESPONSE": dataset['answer'][0]
    }
    system_prompt_msg = msg.format(**param_values)

    # Setup the system prompts and messages to send to the model.
    system_prompts = [{"text": system_prompt_msg}]

    messages = []

    eval_data.append(
        {
            # "id": dataset["id"],
            "QUESTION": dataset['question'][0],
            "EVAL_MODEL": f'{model_family}~{model_name}'
        }
    )

    for metric in metrics:

        if metric in simple_metrics:
            question =  evaluation_utils.get_question_by_simple_metric(metric)
            message = {
                "role": "user",
                "content": [{"text": f"{question}"}]
            }
            messages.append(message)
            response = generate_result(
                bedrock_client, model_name, system_prompts, messages)
            formated_response = {
                'role': 'assistant',
                "content": [{"text": response}]
            }
            messages.append(formated_response)

            value = 1.0 if response.strip(" ").lower() == "yes" else 0.0

            eval_data[-1][metric] = value

    eval_data[-1]["execution_id"] = execution_id
    eval_dataset = pd.DataFrame(eval_data)

    for metric in available_metrics:
        if metric not in eval_dataset.columns:
            eval_dataset[metric] = np.nan
            eval_dataset[metric] = eval_dataset[metric].astype('float64')

    wr.s3.to_parquet(
        df=eval_dataset,
        path=path,
        index=False,
        dataset=True,
        mode="append",
        database=database_name,
        partition_cols=['execution_id'],
        table="llmeval_result"
    )
    return path