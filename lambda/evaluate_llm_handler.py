from ragasutils.prepare_environment import prepare_environment
import sys

directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

from prompts.store import TemplateStore
from handlers.utils.evaluation_util import EvaluationUtils
import pandas as pd
import numpy as np
import boto3
import json
import random
import os
import logging
import pickle

logger = logging.getLogger()
logger.setLevel(logging.INFO)

prompt_template_database = TemplateStore()

from metrics.survey import SurveyMetric
from metrics.cosine import CosineMetric
from prompts.template import PromptTemplate
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

    # Add Prompt Template to the database.
    p_template = PromptTemplate(
        template="""Human: The following is a conversation between a highly knowledgeable and intelligent AI assistant, called Assistant, and a Human user asking Questions. In the following interactions, Assistant will converse in natural language, and Assistant will answer the questions based only on the provided Context. Assistant will provide accurate, short and direct answers to the questions. Answer the below question based on the provided Context, Inquiry and Response.
Context: {CONTEXT}
Inquiry: {INQUIRY}
Response: {RESPONSE}
Question: {QUESTION}
Assistant: """,
        params=["CONTEXT", "INQUIRY", "RESPONSE", "QUESTION"]
    )

    prompt_template_database.add_template(
        template_id="00002",
        template=p_template
    )

    evaluation_utils = EvaluationUtils("SolutionTableDDB")

    simple_metrics = evaluation_utils.get_metric_names_by_type("Simple")
    composed_metrics = evaluation_utils.get_metric_names_by_type("Composed")
    similarity_metrics = evaluation_utils.get_metric_names_by_type("Similarity")

    logger.info("adding simple metrics")

    metrics_to_evaluate = []

    for metric in metrics:

        if metric in simple_metrics:
            logger.info(f"adding simple metric {metric}")
            metrics_to_evaluate.append({
                "metric_name": metric,
                "scoring_object": SurveyMetric(
                    model_family=model_family,
                    model_name=model_name,
                    prompt_template=p_template,
                    questions=[evaluation_utils.get_question_by_simple_metric(metric)]
                )
            })

        if metric in similarity_metrics:
            logger.info(f"adding similarity metric {metric}")
            # At the moment, we only support the cosine metric
            metrics_to_evaluate.append({
                "metric_name": "Cosine Metric",
                "scoring_object": CosineMetric(
                    model_family="bedrock",
                    model_name="amazon.titan-embed-text-v1"
                )
            })

        if metric in composed_metrics:
            logger.info(f"adding composed metric {metric}")
            metrics_to_evaluate.append({
                "metric_name": metric,
                "scoring_object": SurveyMetric(
                    model_family=model_family,
                    model_name=model_name,
                    prompt_template=p_template,
                    questions=evaluation_utils.get_question_by_composed_metric(metric)
                )
            })

    logger.info("begin evaluation")
    eval_data = []


    evals = []
    for metric_ in metrics_to_evaluate:
        # as we use bedrock but it got throttled, we put some sleep time to reduce the tps
        time.sleep(random.randint(0,20))
        metric = metric_["scoring_object"]
        logger.info(f"evaluating metric {metric_['metric_name']}")
        if isinstance(metric, SurveyMetric):
            logger.info("this is a survey metric")
            param_values = {
                "CONTEXT": "".join(dataset['contexts'][0]),
                "INQUIRY": dataset['question'][0],
                "RESPONSE": dataset['answer'][0]
            }
        if isinstance(metric, CosineMetric):
            logger.info("this is a cosine metric")
            param_values = {
                "text1": dataset["answer"][0],
                "text2": dataset["ground_truth"][0]
            }
        score = metric.score(param_values=param_values)
        evals.append({"Key": metric_["metric_name"], "Value": score})

    eval_data.append(
        {
            # "id": dataset["id"],
            "QUESTION": dataset['question'][0],
            "EVAL_MODEL": f'{model_family}~{model_name}'
        }
    )
    for _eval in evals:
        eval_data[-1][_eval["Key"]] = _eval["Value"]
    eval_dataset = pd.DataFrame(eval_data)
    eval_dataset['execution_id'] = execution_id
    path = f"s3://{bucket_name}/llmeval_result/"

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