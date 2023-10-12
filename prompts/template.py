from typing import List

class PromptTemplate:
    def __init__(self, template: str, params: List[str]):
        self.template = template
        self.params = params
    
    def get(self):
        return {
            "template": self.template,
            "params": self.params
        }
    

        