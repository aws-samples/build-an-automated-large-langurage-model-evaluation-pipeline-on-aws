import os
import io
import json
import boto3
from handlers.base import BaseModel, table_name
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
            if line and line[-1] == 10:
                self.read_pos += len(line)
                return line[:-1]
            try:
                chunk = next(self.byte_iterator)
            except StopIteration:
                if self.read_pos < self.buffer.getbuffer().nbytes:
                    continue
                raise
            if 'PayloadPart' not in chunk:
                print(f"Unknown event type: {chunk}")
                continue
            self.buffer.seek(0, io.SEEK_END)
            self.buffer.write(chunk['PayloadPart']['Bytes'])


class model(BaseModel):
    def __init__(self, model_name):
        super().__init__()
        self.endpoint_name = model_name.split(".")[1]
        self.container_type = model_name.split(".")[0]
        self.sagemaker_client = boto3.client(
            service_name="sagemaker-runtime"
        )
        self.invoke_api = self.sagemaker_client.invoke_endpoint
        self.invoke_api_with_response_stream = self.sagemaker_client.invoke_endpoint_with_response_stream
        self.stream_iter = StreamIterator
        if table_name == "":
            schema_path = f"handlers/schemas/sagemaker-{self.container_type}.json"
            if not os.path.exists(schema_path):
                raise NotImplementedError(
                    f"Schema file {schema_path} not found or not implemented."
                )
        else:
            schema_path = f"sagemaker-{self.container_type}"
        (
            self.request_defaults,
            self.request_mapping,
            self.response_regex,
            self.response_mapping,
            self.response_stream_regex,
            self.response_stream_mapping
        ) = self.load_mappings(schema_path)

    def invoke(self, body):
        request_body = self.form_request(
            body,
            self.request_defaults,
            self.request_mapping
        )
        response = self.invoke_api(
            EndpointName=self.endpoint_name,
            Body=json.dumps(request_body).encode("utf-8"),
            ContentType="application/json"
        )
        res_body = response["Body"].read().decode("utf-8")
        res = self.parse_response(
            res_body,
            self.response_mapping,
            self.response_regex
        )
        return res

    def invoke_with_response_stream(self, body):
        try:
            body["stream"] = True
            request_body = self.form_request(
                body, 
                self.request_defaults,
                self.request_mapping
            )
            response = self.invoke_api_with_response_stream(
                EndpointName=self.endpoint_name,
                Body=json.dumps(request_body).encode("utf-8"),
                ContentType="application/json"
            )
            for line in self.stream_iter(response["Body"]):
                if line:
                    output = self.parse_response(
                        line.decode("utf-8"),
                        self.response_stream_mapping,
                        regex_sub=self.response_stream_regex
                    )
                    yield output
        except Exception as e:
            logger.error(f"Error {e}, Body {body}")
            yield {"error": f"Error {e}, Body {body}"}
