from ragasutils.prepare_environment import prepare_environment
import sys
directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)
from datasets import Dataset
from ragasutils.ragas_evaluation import KnowledgeBasesEvaluations
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
    )
import awswrangler as wr

import json
import boto3
import os

import pandas as pd
import numpy as np
import pickle

bucket_name = os.getenv("RESULTBUCKET")
database_name = os.getenv("ResultDatabase")

s3 = boto3.client('s3')
def download_jsonlines_from_s3(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    lines = obj['Body'].read().decode('utf-8').splitlines()
    return lines

def convert_to_dataset(content):
    data = {
            "question": content['question'],
            "answer": content['answer'],
            "contexts": content['contexts'],
            "ground_truth": content['ground_truth']
        }
    dataset = Dataset.from_dict(data)
    return dataset

MODEL_ID_EVAL = "anthropic.claude-3-sonnet-20240229-v1:0"

available_metrics = {
    "faithfulness": faithfulness,
    "answer_relevancy": answer_relevancy,
    "context_recall": context_recall,
    "context_precision": context_precision
}

def lambda_handler(event, context):

    execution_id = event['executionId'].split(":")[-1]
    bucket = event['input']['evaluation_location'].split('/')[2]
    key = '/'.join(event['input']['evaluation_location'].split('/')[3:])
    metrics = event['input']['evaluation_metrics']

    evaluation_metric = [available_metrics[metric] for metric in metrics]

    print(bucket, key)
    path = f"s3://{bucket_name}/ragaseval_result/"
    print(path)
    # download the pickle file from s3
    s3.download_file(bucket, key, "/tmp/result.pickle")

    with open("/tmp/result.pickle", 'rb') as handle:
        content = pickle.load(handle)

    dataset = convert_to_dataset(content)

    evaluator = KnowledgeBasesEvaluations(MODEL_ID_EVAL)
    result_df = evaluator.evaluate(dataset, metrics=evaluation_metric)
    result_df['execution_id'] = execution_id

    # if any of the available metrics is missing, add it with a default value of null and cast to double
    for metric in available_metrics:
        if metric not in result_df.columns:
            result_df[metric] = np.nan
            result_df[metric] = result_df[metric].astype('float64')

    wr.s3.to_parquet(
        df=result_df,
        path=path,
        index=False,
        dataset=True,
        mode="append",
        database=database_name,
        partition_cols=['execution_id'],
        table="ragaseval_result"
    )




