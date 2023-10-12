from prompts.store import TemplateStore
import pandas as pd
from typing import List, Dict
from io import StringIO
import boto3

prompt_template_database = TemplateStore()

from importlib import import_module
from prompts.template import PromptTemplate

from metrics.survey import SurveyMetric
from metrics.cosine import CosineMetric
from prompts.template import PromptTemplate
import awswrangler as wr
import time


def put_string_to_s3(bucket_name, key, content_string):
    s3_client = boto3.client('s3')

    # Put the string content to the specified S3 bucket and key
    response = s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=content_string
    )

    return key


def handler(event, context):
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

    eval_model = {
        "model_family": "bedrock",
        "model_name": "anthropic.claude-v2"
    }

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

    metrics = [
        {
            "metric_name": "Sanity Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[0]]
            )
        },
        {
            "metric_name": "Accuracy Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[1]]
            )
        },
        {
            "metric_name": "Compact Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[2]]
            )
        },
        {
            "metric_name": "Relvency Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[3]]
            )
        },
        {
            "metric_name": "Redundancy Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[4]]
            )
        },
        {
            "metric_name": "Form Check",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=[QUESTIONS[5]]
            )
        },
        {
            "metric_name": "Weighted Score",
            "scoring_object": SurveyMetric(
                model_family=eval_model["model_family"],
                model_name=eval_model["model_name"],
                prompt_template=p_template,
                questions=QUESTIONS
            )
        },
        {
            "metric_name": "Cosine Metric",
            "scoring_object": CosineMetric(
                model_family="bedrock",
                model_name="amazon.titan-embed-text-v1"
            )
        }
    ]

    eval_data = []
    file_location = event['result']
    model_family = event['model_family']
    model_name = event['model_name']
    dataset = wr.s3.read_csv(path=file_location, sep="|")
    for ind in dataset.index:
        evals = []
        time.sleep(10)
        for metric_ in metrics:
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

    output_string = eval_dataset.to_csv(sep='|', index=False)
    bucket_name = "rafaxu-aiml"  # hardcode at the moment
    key = f"llm-evaluation/{model_family}-{model_name}.csv"
    put_string_to_s3(bucket_name, key, output_string)
    return output_string