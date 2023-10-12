from prompts.store import TemplateStore
import pandas as pd
from typing import List, Dict
from io import StringIO
import boto3

prompt_template_database = TemplateStore()

from importlib import import_module
from prompts.template import PromptTemplate


def call_endpoint(payload):
    model = import_module("handlers." + payload["model_family"]).model(payload["model_name"])
    prompt = prompt_template_database.get_prompt_from_template(
        template_id=payload["template_id"],
        param_values=payload["template_params"]
    )
    return model.invoke({"prompt": prompt})["generated_text"]


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
    p_template = PromptTemplate(
        template="""Human: Use the following pieces of context to provide a concise answer to the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
{CONTEXT}

Question: {Question_text}
Assistant:""",
        params=["CONTEXT", "Question_text"]
    )

    prompt_template_database.add_template(
        template_id="00001",
        template=p_template
    )

    data = event['prompts']['prompts']
    dataset = pd.read_csv(StringIO(data), delimiter='|')
    answers = []
    for ind in dataset.index:
        payload = {
            "model_family": event["model_family"],
            "model_name": event["model_name"],
            "template_id": "00001",
            "template_params": {
                "CONTEXT": f"CONTEXT: {dataset['CONTEXT'][ind]}",
                "Question_text": f"{dataset['QUESTION'][ind]}"
            }

        }
        answers.append(call_endpoint(payload))
    dataset["Response"] = answers
    output_string = dataset.to_csv(sep='|', index=False)
    bucket_name = "rafaxu-aiml"  # hardcode at the moment
    key = f"llm-response/{event['model_family']}-{event['model_name']}.csv"
    put_string_to_s3(bucket_name, key, output_string)

    del event['prompts']
    event['result'] = key

    return event