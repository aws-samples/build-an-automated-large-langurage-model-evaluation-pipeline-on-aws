import boto3
from boto3.dynamodb.conditions import Key


class EvaluationUtils:

    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.pk = "EvaluationQuestions"

    # define a function to get item from dynamodb
    def __get_item_from_dynamodb(self, pk, sk):
        response = self.table.get_item(Key={'PK': pk, 'SK': sk})
        return response['Item']

    def get_question_by_simple_metric(self, evaluation_metric):

        response = self.table.get_item(Key={'PK': self.pk, 'SK': f"Simple#" + evaluation_metric})
        result = {}
        if "Item" in response:
            result['Question'] = response['Item']['Question']
            result['Weight'] = int(response['Item']['Weight'])

        return result

    def get_question_by_composed_metric(self, composed_metric):
        response = self.table.get_item(Key={'PK': self.pk, 'SK': f"Composed#" + composed_metric})
        skprefix = response['Item']['SKPrefix']
        all_questions = self.table.query(KeyConditionExpression=Key('PK').eq(self.pk) & Key('SK').begins_with(skprefix + "#"))
        result = [{
            'Question': item['Question'], 'Weight': int(item['Weight'])} for item in all_questions['Items']
        ]
        return result


    def get_all_metrics(self):
        pk = "EvaluationQuestions"
        response = self.table.query(KeyConditionExpression=Key('PK').eq(pk))
        result = [item['SK'].split('#')[1]for item in response['Items']]
        return result


    def get_metric_names_by_type(self, metric_type):
        pk = "EvaluationQuestions"
        response = self.table.query(KeyConditionExpression=Key('PK').eq(pk) & Key('SK').begins_with(metric_type + "#"))
        result = [item['SK'].split('#')[1] for item in response['Items']]
        return result


    def get_fmeval_metric(self):
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq('FMEVALMetric')
        )

        items = response['Items']
        return [item['SK'] for item in items]

    def get_evaluation_template(self):
        # PK is Evaluation, SK is Template
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq('Evaluation') & Key('SK').eq('Template')
        )

        return response['Items'][0]['template']


def main():
    evaluation_utils = EvaluationUtils(table_name='SolutionTableDDB')
    print(evaluation_utils.get_all_metrics())
    template = evaluation_utils.get_evaluation_template()
    context = "SageMaker includes the following machine learning environments: SageMaker Canvas: An auto ML service that gives people with no coding experience the ability to build models and make predictions with them. SageMaker Studio:   An integrated machine learning environment where you can build, train, deploy, and analyze your models all in the same application. SageMaker Studio Lab: A free service that gives customers access to AWS compute resources in an environment based on open-source JupyterLab. RStudio on Amazon SageMaker: An integrated development environment for R, with a console, syntax-highlighting editor that supports direct code execution, and tools for plotting, history, debugging and workspace management."
    inquery = "Does SageMaker provide any free ML environments?"
    response = "Yes, SageMaker does provide a free machine learning environment called SageMaker Studio Lab. This is a service that gives customers access to AWS compute resources in an environment based on open-source JupyterLab, at no charge. SageMaker Studio Lab allows users to get started with machine learning on AWS quickly without needing to configure infrastructure."
    param_values = {
        "CONTEXT": context,
        "INQUIRY": inquery,
        "RESPONSE": response
    }
    result = template.format(**param_values)
    print(result)

if  __name__ == "__main__":
    main()
