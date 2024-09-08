import pandas as pd
import os
import boto3
import json
import pickle
import awswrangler as wr

result_bucket = os.environ['ResultBucket']
s3 = boto3.client('s3')

def handler(event, context):
    failed_result = [item['prompt'] for item in event if "prompt" in item]
    success_result = [item for item in event if "result" in item]
    columns = ["id", "QUESTION", "CONTEXT", "Expected Answer"]
    # for each successful result, read from the s3 path into a object then convert it to json
    execution_id = event[0]['execution_id']
    result_list = []
    for result in success_result:
        s3_path = result['result'].split('//')[1]
        bucket = s3_path.split('/')[0]
        key = '/'.join(s3_path.split('/')[1:])
        dataset_file = f"/tmp/{key.split('/')[-1]}"
        s3.download_file(bucket, key, dataset_file)

        with open(dataset_file, 'rb') as handle:
            dataset = pickle.load(handle)

        result_list.append(dataset)

    with open('/tmp/output.jsonl', 'w') as jsonl_file:
        for item in result_list:
            jsonl_file.write(json.dumps(item) + '\n')

    key = f"invoke_successful_result/jsonline/{execution_id}/result.jsonl"
    # write the result_json as a string to S3
    s3.upload_file("/tmp/output.jsonl", result_bucket, key)

    result = {
        "success_result": f"s3://{result_bucket}/{key}"
    }
    # handle the failed result for re-use
    if len(failed_result) > 0:
        split_data = [item.split('|') for item in failed_result]
        print(len(split_data))
        # write the failed_result to S3
        wr.s3.to_csv(df=pd.DataFrame(split_data, columns=columns),
                     path=f's3://{result_bucket}/invoke_failed_result/{execution_id}/failed_question.csv', header=True,
                     sep='|',
                     index=False)
        result["failed_result"] = f"s3://{result_bucket}/invoke_failed_result/{execution_id}/failed_question.csv"

    return result