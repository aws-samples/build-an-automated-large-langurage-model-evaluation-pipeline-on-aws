from typing import Dict
import time

class BaseMetric:

    def score(self):
        raise NotImplementedError("Feature not implemented in Base class")

    def handler(self, prompt):
        return self.model.invoke({"prompt": prompt})["generated_text"]

    def get_prompt_from_template(self, template: str, params_values: Dict[str, str]):
        record = self.database[template_id]
        
        kwargs = {}
        for param in record["params"]:
            kwargs[param] = params_values[param]
        return record["template"].format(**kwargs)