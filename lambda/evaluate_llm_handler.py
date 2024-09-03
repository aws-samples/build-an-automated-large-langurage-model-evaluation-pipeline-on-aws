from prompts.store import TemplateStore
from handlers.utils.evaluation_util import EvaluationUtils
import pandas as pd
import boto3
import json
import random
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

prompt_template_database = TemplateStore()

from importlib import import_module
from prompts.template import PromptTemplate

from metrics.survey import SurveyMetric
from metrics.cosine import CosineMetric
from prompts.template import PromptTemplate
import awswrangler as wr
import time


def handler(event, context):
    logger.info(f"receiving event {event}")
    bucket_name = os.getenv("ResultBucket")
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

    execution_id = event['execution_id'].split(":")[-1]
    event = event["input"]

    logger.info(f"event input: {event}")

    metrics = event['evaluation_metrics']

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
                    model_family=event["model_family"],
                    model_name=event["model_name"],
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
                    model_family=event["model_family"],
                    model_name=event["model_name"],
                    prompt_template=p_template,
                    questions=evaluation_utils.get_question_by_composed_metric(metric)
                )
            })


    logger.info("begin evaluation")
    eval_data = []
    question_answer = event['evaluation_question_answer'].replace("'",'"')
    model_family = event['model_family']
    model_name = event['model_name']

    dataset = json.loads(question_answer)
    evals = []
    for metric_ in metrics_to_evaluate:
        # as we use bedrock but it got throttled, we put some sleep time to reduce the tps
        time.sleep(random.randint(0,10))
        metric = metric_["scoring_object"]
        logger.info(f"evaluating metric {metric_['metric_name']}")
        if isinstance(metric, SurveyMetric):
            logger.info("this is a survey metric")
            param_values = {
                "CONTEXT": dataset['CONTEXT'],
                "INQUIRY": dataset['QUESTION'],
                "RESPONSE": dataset['Response']
            }
        if isinstance(metric, CosineMetric):
            logger.info("this is a cosine metric")
            param_values = {
                "text1": dataset["Response"],
                "text2": dataset["ExpectedAnswer"]
            }
        score = metric.score(param_values=param_values)
        evals.append({"Key": metric_["metric_name"], "Value": score})
    eval_data.append(
        {
            "id": dataset["id"],
            "QUESTION": dataset["QUESTION"],
            # "CONTEXT": dataset["CONTEXT"][ind],
            # "Expected Answer": dataset["Expected Answer"][ind],
            # "Response": dataset["Response"][ind],
            "EVAL_MODEL": f'{model_family}~{model_name}'
        }
    )
    for _eval in evals:
        eval_data[-1][_eval["Key"]] = _eval["Value"]
    eval_dataset = pd.DataFrame(eval_data)
    output_string = eval_dataset.to_csv(sep='|', index=False, header=False)
    key = f"llm-evaluation/{execution_id}/{model_family}-{model_name}.csv"
    return output_string