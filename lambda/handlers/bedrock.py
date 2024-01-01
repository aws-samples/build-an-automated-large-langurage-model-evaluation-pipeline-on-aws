import os
import json
import boto3
from handlers.base import BaseModel
from log.logger import logger

embedding_models = [
    "amazon.titan-e1t-medium",
    "amazon.titan-embed-g1-text-02",
    "amazon.titan-embed-text-v1"
]

class model(BaseModel):
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
        self.bedrock_client = boto3.client(
            service_name="bedrock-runtime", 
            region_name="us-west-2"
        )
        self.invoke_api = self.bedrock_client.invoke_model
        schema_path = f'handlers/schemas/bedrock-{model_name.split(".")[0]}.json'
        if model_name in embedding_models:
            schema_path = f'handlers/schemas/bedrock-{model_name.split(".")[0]}-embedding.json'
        if os.path.exists(schema_path):
            (
                self.request_defaults,
                self.request_mapping,
                self.response_mapping
            ) = self.load_mappings(schema_path)
        else:
            raise NotImplementedError(f"Schema file {schema_path} not found or not implemented.")

    def invoke(self, body):
        try:
            request_body = self.form_request(
                body, 
                self.request_defaults, 
                self.request_mapping
            )
            response = self.invoke_api(
                modelId=self.model_name,
                body = json.dumps(request_body).encode("utf-8")
            )
            res = self.parse_response(
                json.loads(response["body"].read()),
                self.response_mapping
            )
            return res
        except Exception as e:
            logger.error(f"Error {e}, Body {body}")
            raise e
        