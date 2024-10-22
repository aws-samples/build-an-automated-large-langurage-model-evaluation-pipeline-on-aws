from llmeter.endpoints import BedrockConverse, BedrockConverseStream
from llmeter.runner import Runner
import asyncio
from upath import UPath  # Combined APIs for accessing cloud or local storage
import boto3
import json
import awswrangler as wr

model_id = "anthropic.claude-3-haiku-20240307-v1:0"
import os

bucket_name = os.getenv("ResultBucket")
database_name = os.getenv("ResultDatabase")


def parse_s3_location(location):
    """Parse s3 URL into bucket and prefix."""
    print(location)
    if not location.startswith("s3://"):
        raise ValueError("Invalid S3 URL")

    path_parts = location[5:].split("/", 1)  # strip off 's3://' and split by the first /
    bucket = path_parts[0]

    if len(path_parts) == 1:
        raise Exception("Invalid S3 URL")
    prefix = path_parts[1]

    if not prefix.endswith(".jsonl"):
        raise Exception("Invalid S3 URL")

    return bucket, prefix


def object_exists(s3_client, bucket, key):
    """Check if an object exists by trying to retrieve metadata about the object."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.ClientError as e:
        return False


bedrock_endpoint = BedrockConverse(
    model_id=model_id,
    # Optionally, you can target a different AWS Region than your default:
    # region="us-west-2",
)


def get_converse_payload(context, question, max_token=512):
    return {"user_message": question,
            "max_tokens": max_token,
            "system": [{
                "text": "You are an smart AI assistant to provide a concise answer to the question to user, use the context provided, If you don't know the answer, just say that you don't know, don't try to make up an answer. Below is the context"
                        f"{context}"}]
            }


s3_client = boto3.client('s3')


def read_jsonl_generator(file_path):
    with open(file_path, 'r') as jsonl_file:
        for line in jsonl_file:
            yield json.loads(line.strip())


async def handler(event, context):
    print(event)

    if "evaluation_location" not in event:
        raise Exception("evaluation_location is required")

    if "evaluation_model_name" not in event:
        raise Exception("no evaluation_model_name in event")

    s3_location = event["evaluation_location"]

    bucket, key = parse_s3_location(s3_location)
    key_path = '/'.join(key.split('/')[:-1])
    if not object_exists(s3_client, bucket, key):
        raise Exception("evaluation_location does not exist")

    # download the jsonl file from s3 and split them into pickle files
    s3_client.download_file(bucket, key, '/tmp/input.jsonl')

    payload_list = []
    for item in read_jsonl_generator('/tmp/input.jsonl'):
        question = item["QUESTION"][0]
        context = ".".join(item['CONTEXT'][0])

        # Process each item (dictionary) here
        payload = get_converse_payload(context, question)
        print(payload)
        sample_payload = BedrockConverse.create_payload(**payload)
        payload_list.append(sample_payload)

    endpoint_test = Runner(
        bedrock_endpoint,
        output_path=f"/tmp/{bedrock_endpoint.model_id}",
    )

    results = await endpoint_test.run(payload=sample_payload, n_requests=3, clients=3)

    path = f"s3://{bucket_name}/llmeter_result/"

    result_df = wr.pandas.DataFrame([results])
    result_df['execution_id'] = context.request_id

    wr.s3.to_parquet(
        df=result_df,
        path=path,
        index=False,
        dataset=True,
        mode="append",
        database=database_name,
        partition_cols=['execution_id'],
        table="llmeter_result"
    )

    return {"foo": "bar"}


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(handler(event, context))
