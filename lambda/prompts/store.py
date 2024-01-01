from typing import List, Dict
from prompts.template import PromptTemplate

class TemplateStore:
    database = {}
    def __init__(self, external_store: bool=False, ddb_table_name: str=""):
        self.external_store = external_store
        if external_store:
            if ddb_table_name=="":
                raise ValueError("Must supply valid ddb_table_name for external store")
            else:
                self.table_name = ddb_table_name
        
    def add_template(self, template_id: str, template: PromptTemplate):
        self.database[template_id] = template
        if self.external_store:
            # TODO: Add template to DDB table
            pass
    
    def get_prompt_from_template(self, template_id: str, param_values: Dict[str, str]):
        if self.external_store:
            if template_id not in self.database:
                # TODO: Get template from DDB
                raise NotImplementedError("DDB store not implemented yet")
        else:
            record = self.database[template_id]
        
        kwargs = {}
        for param in record.params:
            kwargs[param] = param_values[param]
        return record.template.format(**kwargs)

