from importlib import import_module
import argparse
import json
import logging as logger
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from handlers.base import table_name, ddb_client

import uvicorn

app = FastAPI()

# health check
@app.get("/ping")
def ping():
    return {"Health_Check": "200"}

@app.get("/list_models")
def list_models():
    if table_name == "":
        all_models_file_path = "handlers/schemas/all-models.json"
        with open(all_models_file_path, "r") as all_models_file:
            all_models = json.load(all_models_file)
            return {"models": all_models}
    else:
        all_models = ddb_client.get_item(
            TableName=table_name,
            Key={
                "model_id": {
                    "S": "all-models"
                }
            }
        )["Item"]["models"]["S"]
        return {"models": json.loads(all_models)}

@app.post("/invoke")
async def invoke(request: Request):
    params = await request.json()
    model_family = params.get("model_family")
    model_name = params.get("model_name")
    body = params.get("body")
    if not (model_family and model_name and body):
        raise
    try:
        invoke_model = import_module("handlers." + model_family).model(model_name).invoke
        return invoke_model(body)

    except Exception as e:
        # Handle any exceptions that occur during execution
        return {"error": f"An error occurred: {str(e)}" }
    
async def invoke_with_response_stream(stream_response):
    for next_item in stream_response:
        # if "generated_text"  in next_item and next_item["generated_text"] != "<EOS_TOKEN>":
        yield json.dumps(next_item) + "\n"
        
@app.post("/invoke_stream")
async def invoke_stream(request: Request):
    params = await request.json()
    model_family = params.get("model_family")
    model_name = params.get("model_name")
    body = params.get("body")
    if not (model_family and model_name and body):
        raise
    try:
        invoke_model = import_module("handlers." + model_family).model(model_name).invoke_with_response_stream
        return StreamingResponse(
            invoke_with_response_stream(
                invoke_model(body)
            ), 
            media_type="application/x-ndjson"
        )
    except Exception as e:
        # Handle any exceptions that occur during execution
        return {"error": f"An error occurred: {str(e)}"}

    
if __name__ == "__main__":  
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--table-name", type=str, default="")
    args = parser.parse_args()
    table_name = args.table_name
    print(table_name)
    logger.info(f"args: {args}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")