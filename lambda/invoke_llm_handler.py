from prompts.store import TemplateStore
import pandas as pd
import os
import boto3
import awswrangler as wr

prompt_template_database = TemplateStore()

from importlib import import_module
from prompts.template import PromptTemplate
from llm_api.invoke_llm import get_llm_result


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

    bucket_name = os.getenv("ResultBucket")
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

    # the format is id|question|context|response
    # we need to split the string using | as the seperator
    prompt = event['prompt']
    model_family = event['invoke_model_family']
    model_name = event['invoke_model_name']
    execution_id = event['execution_id']

    prompts_list = prompt.split('|')

    payload = {
        "model_family": model_family,
        "model_name": model_name,
        "template_id": "00001",
        "template_params": {
            "CONTEXT": f"CONTEXT: {prompts_list[2]}",
            "Question_text": f"{prompts_list[1]}"
        }
    }

    prompt = prompt_template_database.get_prompt_from_template(
        template_id=payload["template_id"],
        param_values=payload["template_params"]
    )

    answer = get_llm_result(prompt, model_family, model_name)
    data = {'id': [prompts_list[0]], 'QUESTION': [prompts_list[1]], 'CONTEXT': [prompts_list[2]],
            'Expected Answer': [prompts_list[3]], 'Response': [answer]}
    df = pd.DataFrame(data)

    key = f"llm-response/{execution_id}/{prompts_list[0]}_{model_family}-{model_name}.csv"
    wr.s3.to_csv(
        df=df,
        path=f"s3://{bucket_name}/{key}",
        index=False,
        sep="|"
    )
    del event['prompt']
    event['result'] = f"s3://{bucket_name}/{key}"

    return event