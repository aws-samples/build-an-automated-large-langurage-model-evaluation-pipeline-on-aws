import os
import json
import boto3
from handlers.base import BaseModel

class model(BaseModel):
    def __init__(self, model_name):
        super().__init__()
        self.endpoint_name = model_name.split(".")[1]
        self.container_type = model_name.split(".")[0]
        self.sagemaker_client = boto3.client(
            service_name="sagemaker-runtime"
        )
        self.invoke_api = self.sagemaker_client.invoke_endpoint
        schema_path = f'handlers/schemas/sagemaker-{self.container_type}.json'
        if os.path.exists(schema_path):
            (
                self.request_defaults,
                self.request_mapping,
                self.response_mapping
            ) = self.load_mappings(schema_path)
        else:
            raise NotImplementedError(f"Schema file {schema_path} not found or not implemented.")

    def invoke(self, body):
        request_body = self.form_request(
            body, 
            self.request_defaults, 
            self.request_mapping
        )
        response = self.invoke_api(
            EndpointName=self.endpoint_name,
            Body = json.dumps(request_body).encode("utf-8"),
            ContentType="application/json"
        )
        res_body = response["Body"].read().decode("utf-8")
        res = self.parse_response(
            json.loads(res_body),
            self.response_mapping
        )
        return res