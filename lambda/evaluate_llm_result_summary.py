import json
import pandas as pd
import awswrangler as wr
import os
bucket_name = os.getenv("ResultBucket")
database_name = os.getenv("ResultDatabase")

def list_to_dataframe(input_list, columns):
    processed_list = [item.strip().split('|') for item in input_list]
    df = pd.DataFrame(processed_list, columns=columns)
    return df


def handler(event, context):
    print(event)
    execution_id = event['executionId'].split(":")[-1]
    event = event['input']
    if len(event) == 0:
        return "Nonthing"
    evaluation_metrics = event[0]['evaluation_metrics']
    model_family = event[0]['model_family']
    model_name = event[0]['model_name']

    columns = ['ID', "Question", "Model"] + evaluation_metrics

    input_list = [e['result']['result'] for e in event if 'evaluation_metrics' in e]
    df = list_to_dataframe(input_list, columns)
    df['execution_id'] = execution_id

    path = "llmeval_result/"
    # wr.s3.to_csv(
    #     df=df,
    #     path=f"s3://{bucket_name}/{key}",
    #     index=False,
    #     sep=","
    # )

    wr.s3.to_parquet(
        df=df,
        path=f"s3://{bucket_name}/{path}",
        index=False,
        dataset=True,
        mode="append",
        database=database_name,
        partition_cols=['execution_id'],
        table="llmeval_result"
    )

    return ["|".join(columns)] + input_list
