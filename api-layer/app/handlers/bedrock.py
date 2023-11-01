import os
import io
import json
import boto3
from handlers.base import BaseModel
import logging as logger

class StreamIterator:
    def __init__(self, stream):
        self.byte_iterator = iter(stream)
        self.buffer = io.BytesIO()
        self.read_pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            self.buffer.seek(self.read_pos)
            line = self.buffer.readline()
            if line:
                self.read_pos += len(line)
                return line
            try:
                chunk = next(self.byte_iterator)
            except StopIteration:
                if self.read_pos < self.buffer.getbuffer().nbytes:
                    continue
                raise
            if 'chunk' not in chunk:
                print(f"Unknown event type: {chunk}")
                continue
            self.buffer.seek(0, io.SEEK_END)
            self.buffer.write(chunk['chunk']['bytes'])

class model(BaseModel):
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
        self.bedrock_client = boto3.client(
            service_name="bedrock-runtime", 
            region_name="us-west-2"
        )
        self.invoke_api = self.bedrock_client.invoke_model
        self.invoke_api_with_response_stream = self.bedrock_client.invoke_model_with_response_stream
        self.stream_iter = StreamIterator
        schema_path = f'handlers/schemas/bedrock-{model_name.split(".")[0]}.json'
        if os.path.exists(schema_path):
            (
                self.request_defaults,
                self.request_mapping,
                self.response_regex,
                self.response_mapping,
                self.response_stream_regex,
                self.response_stream_mapping
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
                body=json.dumps(request_body).encode("utf-8")
            )
            res = self.parse_response(
                response["body"].read(),
                self.response_mapping,
                regex_sub=self.response_regex
            )
            return res
        except Exception as e:
            logger.error(f"Error {e}, Body {body}")
            raise e
            
    def invoke_with_response_stream(self, body):
        try:
            body["stream"] = True
            request_body = self.form_request(
                body, 
                self.request_defaults, 
                self.request_mapping
            )
            response = self.invoke_api_with_response_stream(
                modelId=self.model_name,
                body = json.dumps(request_body).encode("utf-8")
            )
            for line in self.stream_iter(response["body"]):
                if line:
                    output = self.parse_response(
                        line,
                        self.response_stream_mapping,
                        regex_sub=self.response_stream_regex
                    )
                yield output
        except Exception as e:
            logger.error(f"Error {e}, Body {body}")
            raise e
        