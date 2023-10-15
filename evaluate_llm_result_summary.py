import json
import pandas as pd
import awswrangler as wr
import os


def list_to_dataframe(input_list, columns):
    processed_list = [item.strip().split('|') for item in input_list]
    df = pd.DataFrame(processed_list, columns=columns)
    return df


def handler(event, context):
    if len(event) == 0:
        return "Nonthing"
    evaluation_metrics = event[0]['evaluation_metrics']
    model_family = event[0]['model_family']
    model_name = event[0]['model_name']

    columns = ['ID', "Question", "Model"] + evaluation_metrics

    input_list = [e['result']['result'] for e in event]
    df = list_to_dataframe(input_list, columns)
    bucket_name = os.getenv("ResultBucket")
    key = f"llm-response/mytesting/{model_family}-{model_name}.csv"
    wr.s3.to_csv(
        df=df,
        path=f"s3://{bucket_name}/{key}",
        index=False,
        sep="|"
    )
    return ["|".join(columns)] + input_list
