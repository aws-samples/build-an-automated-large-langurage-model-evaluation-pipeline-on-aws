import json
import boto3
from numpy import dot
from numpy.linalg import norm
from typing import List, Dict
from metrics.base import BaseMetric
from importlib import import_module
from log.logger import app_logger

logger = app_logger()

class CosineMetric(BaseMetric):
    def __init__(
        self,
        model_family: str,
        model_name: str,
    ):
        self.model_family = model_family
        self.model_name = model_name
        self.model = import_module("handlers." + model_family).model(model_name)
        
    def handler(self, prompt):
        return self.model.invoke({"prompt": prompt})["embedding"]
        
    def get_embedding(self, text):
        return self.handler(text)

    def calculate_cousine_similarity(self, v1, v2):
        similarity = dot(v1, v2)/(norm(v1)*norm(v2))
        return similarity
    
    def score(self, param_values: Dict[str, str]):
        return self.calculate_cousine_similarity(
            self.get_embedding(param_values["text1"]),
            self.get_embedding(param_values["text2"])
        )
            