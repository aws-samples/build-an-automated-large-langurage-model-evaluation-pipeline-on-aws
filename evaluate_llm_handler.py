from prompts.store import TemplateStore
import pandas as pd
import boto3
import random
import os

prompt_template_database = TemplateStore()

from importlib import import_module
from prompts.template import PromptTemplate

from metrics.survey import SurveyMetric
from metrics.cosine import CosineMetric
from prompts.template import PromptTemplate
import awswrangler as wr
import time


def handler(event, context):
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

    eval_model = {
        "model_family": event['model_family'],
        "model_name": event['model_name']
    }

    metrics = event['evaluation_metrics']

    QUESTIONS = [
        {
            "Question": "Is the above response based solely on the provided context? Answer with Yes or No only.",
            "Weight": 20
        },
        {
            "Question": "Based solely on the provided context, is the above response accurately answers the Inquiry? Answer with Yes or No only.",
            "Weight": 20
        },
        {
            "Question": "Is the above response short, compact and direct? Answer with Yes or No only.",
            "Weight": 10
        },
        {
            "Question": "The above response does not have any words that can be removed without imapcting its meaning, is that true? Answer with Yes or No only.",
            "Weight": 10
        },
        {
            "Question": "Is the above response an answer or a question? Answer only with Yes if it is an answer or No if it is a question.",
            "Weight": 30
        },
        {
            "Question": "The above response does not mention the word `context` in reference to the above provided context, is that true? Answer with Yes or No only.",
            "Weight": 10
        }
    ]

    metric_question_dict = {
        "Sanity Check": [QUESTIONS[0]],
        "Accuracy Check": [QUESTIONS[1]],
        "Compact Check": [QUESTIONS[2]],
        "Relevancy Check": [QUESTIONS[3]],
        "Redundancy Check": [QUESTIONS[4]],
        "Form Check": [QUESTIONS[5]],
        "Weighted Score": QUESTIONS
    }

    metrics_to_evaluate = [
        {
            "metric_name": metric,
            "scoring_object": SurveyMetric(
                model_family=event["model_family"],
                model_name=event["model_name"],
                prompt_template=p_template,
                questions=metric_question_dict[metric]
            )
        } for metric in metrics if metric != "Cosine Metric"]

    if "Cosine Metric" in metrics:
        metrics_to_evaluate.append({
            "metric_name": "Cosine Metric",
            "scoring_object": CosineMetric(
                model_family="bedrock",
                model_name="amazon.titan-embed-text-v1"
            )
        })

    eval_data = []
    file_location = event['evaluation_location']
    model_family = event['model_family']
    model_name = event['model_name']
    dataset = wr.s3.read_csv(path=file_location, sep="|")
    print(dataset.shape)
    for ind in dataset.index:
        evals = []
        time.sleep(random.randint(0, 5))
        for metric_ in metrics_to_evaluate:
            metric = metric_["scoring_object"]
            if isinstance(metric, SurveyMetric):
                param_values = {
                    "CONTEXT": f"{dataset['CONTEXT'][ind]}",
                    "INQUIRY": f"{dataset['QUESTION'][ind]}",
                    "RESPONSE": f"{dataset['Response'][ind]}"
                }
            if isinstance(metric, CosineMetric):
                param_values = {
                    "text1": dataset["Response"][ind],
                    "text2": dataset["Expected Answer"][ind]
                }
            score = metric.score(param_values=param_values)
            evals.append({"Key": metric_["metric_name"], "Value": score})
        eval_data.append(
            {
                "id": dataset["id"][ind],
                "QUESTION": dataset["QUESTION"][ind],
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