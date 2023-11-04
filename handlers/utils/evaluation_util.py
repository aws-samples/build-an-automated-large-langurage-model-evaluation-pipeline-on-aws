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


