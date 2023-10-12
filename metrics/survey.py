from typing import List, Dict
from metrics.base import BaseMetric
from prompts.template import PromptTemplate
from prompts.store import TemplateStore
from importlib import import_module
from log.logger import app_logger

template_id = "survey template"
logger = app_logger()

class SurveyMetric(BaseMetric):
    def __init__(self, 
                 model_family: str,
                 model_name: str, 
                 prompt_template: PromptTemplate,
                 questions: List[Dict[str, int]]=None
                ):
        self.total_weight = 0
        self.questions = []
        self.model_family = model_family
        self.model_name = model_name
        self.model = import_module("handlers." + model_family).model(model_name)
        if not "QUESTION" in prompt_template.params:
            raise ValueError("Provided prompt template does not have 'QUESTION` parameter")
        self.template = TemplateStore()
        self.template.add_template(
            template_id=template_id,
            template=prompt_template
        )
        if questions:
            self.add_questions(questions)
        
    def add_question(self, question: str, weight: str=10):
        self.questions.append(
            {
                "Question": question,
                "Weight": weight
            }
        )
        self.total_weight += weight
        
    def add_questions(self, questions: List[Dict[str, int]]):
        for question in questions:
            self.add_question(
                question=question["Question"],
                weight=question["Weight"]
            )
    
    def score(self, param_values: Dict[str, str]):
        score = 0
        for question in self.questions:
            param_values["QUESTION"] = question["Question"]
            prompt = self.template.get_prompt_from_template(
                template_id=template_id,
                param_values=param_values
            )
            answer = self.handler(prompt)
            if answer.strip(" ").lower() == "yes":
                    score += question["Weight"]
        return score / self.total_weight
            