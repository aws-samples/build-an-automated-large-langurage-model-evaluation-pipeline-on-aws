import json
import os
import boto3

# Initialize AWS clients
sfn_client = boto3.client('stepfunctions')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    # Get the operation from the event
    payload = json.loads(event['body'])

    operation = payload.pop("operation")

    if operation not in ['invoke', 'evaluate']:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid operation'})
        }

    stateMachineArn = os.environ['INVOKE_STATE_MACHINE_ARN'] if operation=="invoke" else  os.environ['EVALUATE_STATE_MACHINE_ARN']

    # invoke the step function
    response = sfn_client.start_execution(
        stateMachineArn=stateMachineArn,
        input=json.dumps(payload)
    )

    execution_arn = response['executionArn']


    # Return the Step Function execution ARN to API Gateway
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTION'
        },
        'body': json.dumps({'executionArn': execution_arn})
    }
