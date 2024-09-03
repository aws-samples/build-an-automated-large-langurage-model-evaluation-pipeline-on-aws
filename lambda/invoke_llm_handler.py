from ragas.prepare_environment import prepare_environment
import sys
directory_to_extract_to = prepare_environment()
# update path, so that dependencies can be found
sys.path.insert(0, directory_to_extract_to)

from prompts.store import TemplateStore
from ragas.generate_answer_from_kb import KnowledgeBasesGenerateAnswer
import pandas as pd
import os
import time
import random

import awswrangler as wr

prompt_template_database = TemplateStore()

from prompts.template import PromptTemplate
from llm_api.invoke_llm import get_llm_result

# setup environment variables
bucket_name = os.environ.get('ResultBucket')
kb_id = os.environ.get('KB_ID')


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
    # the format is id|question|context|response
    # we need to split the string using | as the seperator
    prompt = event['prompt']
    model_family = event['model_family']
    model_name = event['model_name']
    execution_id = event['execution_id']

    # add some idle time to reduce the throttle possibility
    time.sleep(random.randint(10,20))

    generation_method = event.get("method", "native")

    prompts_list = prompt.split('|')
    question_id = prompts_list[0]
    question = prompts_list[1]
    context = prompts_list[2]
    expected_answer = prompts_list[3]

    if generation_method == "native":
        answer = get_answer_from_api(model_family, model_name, context, question)
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': [context],
                'Expected Answer': [expected_answer], 'Response': [answer]}
    elif generation_method == "kb":
        if model_family != "bedrock":
            raise ValueError("Only bedrock model family is supported for knowledge base generation")
        kb_generate_answer = KnowledgeBasesGenerateAnswer(model_name, kb_id)
        answer_and_context = kb_generate_answer.get_answer_and_context(question)
        print(answer_and_context)
        data = {'id': [question_id], 'QUESTION': [question], 'CONTEXT': answer_and_context['context'],
                'Expected Answer': [expected_answer], 'Response': [answer_and_context['answer']]}


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