from ragasutils.prepare_environment import prepare_environment
import sys

import boto3

directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

from prompts.store import TemplateStore
from ragasutils.generate_answer_from_kb import KnowledgeBasesGenerateAnswer
import pandas as pd
import os
import time
import random
import pickle

import awswrangler as wr

prompt_template_database = TemplateStore()

from prompts.template import PromptTemplate
from llm_api.invoke_llm import get_llm_result

# setup environment variables
bucket_name = os.environ.get('ResultBucket')
kb_id = os.environ.get('KB_ID')

s3 = boto3.client('s3')


def get_answer_from_api(model_family, model_name, context, question):
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

    payload = prompt_template_database.get_prompt_from_template(
        template_id="00001",
        param_values={
            "CONTEXT": f"CONTEXT: {context}",
            "Question_text": f"{question}"
        }
    )

    answer = get_llm_result(payload, model_family, model_name)
    return answer


def handler(event, context):
    print(event)
    prompt = event['prompt']
    model_family = event['model_family']
    model_name = event['model_name']
    execution_id = event['execution_id']

    generation_method = event.get("method", "native")

    prompts_list = prompt.split('|')
    question_id = prompts_list[0]
    question = prompts_list[1]
    context = prompts_list[2]
    expected_answer = prompts_list[3]

    if generation_method == "native":
        # add some idle time to reduce the throttle possibility
        time.sleep(random.randint(0, 10))
        answer = get_answer_from_api(model_family, model_name, context, question)
    elif generation_method == "kb":
        # add some idle time to reduce the throttle possibility
        time.sleep(random.randint(0, 20))
        if model_family != "bedrock":
            raise ValueError("Only bedrock model family is supported for knowledge base generation")
        kb_generate_answer = KnowledgeBasesGenerateAnswer(model_name, kb_id)
        answer_and_context = kb_generate_answer.get_answer_and_context(question)
        answer = answer_and_context['answer']
        context = answer_and_context['context']
        context_list = [[c] for c in context]
    else:
        raise ValueError("Invalid generation method")

    if generation_method == "native":
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': [[context]],
                'ExpectedAnswer': [expected_answer], 'Response': [answer]}
    else:
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': context_list,
                'ExpectedAnswer': [expected_answer], 'Response': [answer]}

    file_name = f"{prompts_list[0]}_{model_family}-{model_name}.pickle"
    file = f"/tmp/{file_name}"
    key = f"llm-response/{execution_id}/{file_name}"
    with open(file, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"upload file {file} to {bucket_name} in {key}")
    s3.upload_file(file, bucket_name, key)

    del event['prompt']

    event['result'] = f"s3://{bucket_name}/{key}"

    return event