import pandas as pd
import awswrangler as wr
import os
import boto3
import json

bucket = os.environ['ResultBucket']
s3 = boto3.client('s3')


def handler(event, context):
    failed_result = [item['prompt'] for item in event if "prompt" in item]
    success_result = [item for item in event if "result" in item]
    columns = ["id", "QUESTION", "CONTEXT", "Expected Answer"]
    # for each successful result, read from the s3 path into a dataframe then convert it to json
    result_json = []
    execution_id = event[0]['execution_id']
    for result in success_result:
        df = wr.s3.read_csv(path=result['result'], sep='|')

        df.rename(columns={"Expected Answer": "ExpectedAnswer"}, inplace=True)
        for _, row in df.iterrows():
            json_str = json.dumps(row.to_dict(), ensure_ascii=False)
            result_json.append(json_str)

    success_result_as_jsonl = "\n".join(result_json)

    key = f"invoke_successful_result/jsonline/{execution_id}/result.jsonl"
    # write the result_json as a string to S3
    s3.put_object(Bucket=bucket, Key=key, Body=success_result_as_jsonl)

    result = {
        "success_result": f"s3://{bucket}/{key}"
    }
    if len(failed_result) > 0:
        split_data = [item.split('|') for item in failed_result]
        print(len(split_data))
        # write the failed_result to S3
        wr.s3.to_csv(df=pd.DataFrame(split_data, columns=columns),
                     path=f's3://{bucket}/invoke_failed_result/{execution_id}/failed_question.csv', header=True,
                     sep='|',
                     index=False)
        result["failed_result"] = f"s3://{bucket}/invoke_failed_result/{execution_id}/failed_question.csv"

    return result