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
from llm_api.invoke_llm import generate_result

# setup environment variables
bucket_name = os.environ.get('ResultBucket')
kb_id = os.environ.get('KB_ID')

s3 = boto3.client('s3')
bedrock_client = boto3.client(service_name='bedrock-runtime')
bedrock_agent_client = boto3.client('bedrock-agent')


def get_answer_from_api_with_prompt_id(model_name, context, question, prompt_id):
    
    prompt_from_bedrock = bedrock_agent_client.get_prompt(
            promptIdentifier=prompt_id,
        )
    
    prompt_text = prompt_from_bedrock["variants"][-1]['templateConfiguration']['text']['text']
    
    temperature = prompt_from_bedrock["variants"][-1]['inferenceConfiguration']['text'].get("temperature", 0.0)
    topP = prompt_from_bedrock["variants"][-1]['inferenceConfiguration']['text'].get("topP", 0.9)
    maxTokens = prompt_from_bedrock["variants"][-1]['inferenceConfiguration']['text'].get("maxTokens", 4096)
    
    formatted_prompt_template = prompt_text.replace("{{", "{").replace("}}", "}").format( context = context)

    formatted_prompt_template = formatted_prompt_template + "\nQuestion: " + question
    
    message = {
        "role": "user",
        "content": [{"text": formatted_prompt_template}]
    }

    messages = [message]
    
    answer = generate_result(bedrock_client, model_name, None, messages,  temperature = temperature,  topP = topP, maxTokens = maxTokens)

    return answer



def get_answer_from_api(model_name, context, question):
    
    
    system_prompts = [{"text": "You are an smart AI assistant to provide a concise answer to the question to user, use the context provided, If you don't know the answer, just say that you don't know, don't try to make up an answer. Below is the context"
              f"{context}"}]

    message = {
        "role": "user",
        "content": [{"text": question}]
    }

    messages = []
    messages.append(message)

    answer = generate_result(bedrock_client, model_name, system_prompts, messages)

    return answer


def handler(event, context):
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
        answer = get_answer_from_api(model_name, context, question)
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': [[context]],
                'ExpectedAnswer': [expected_answer], 'Response': [answer]}
    elif generation_method == "kb":
        # add some idle time to reduce the throttle possibility
        time.sleep(random.randint(0, 20))
        if model_family != "bedrock":
            raise ValueError("Only bedrock model family is supported for knowledge base generation")
        kb_generate_answer = KnowledgeBasesGenerateAnswer(model_name, kb_id)
        answer_and_context = kb_generate_answer.get_answer_and_context(question)
        answer = answer_and_context['answer']
        context = answer_and_context['context']
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': [context],
                'ExpectedAnswer': [expected_answer], 'Response': [answer]}
    else:
        raise ValueError("Invalid generation method")

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