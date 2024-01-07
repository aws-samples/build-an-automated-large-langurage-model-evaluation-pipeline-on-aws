#!/bin/bash

# Check if region parameter is passed
if [ -n "$AWS_DEFAULT_REGION" ]; then
  echo "AWS_DEFAULT_REGION is set, using $AWS_DEFAULT_REGION for the AWS region"
  REGION=$AWS_DEFAULT_REGION
else
  REGION=$(aws configure get region)
  echo "AWS_DEFAULT_REGION is not set, use $REGION for the aws region"
fi

# Get account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bucket name
SETUPBUCKET="eval-$ACCOUNT_ID-$REGION"

# Check if bucket exists
if ! aws s3api head-bucket --bucket $SETUPBUCKET --region $REGION 1>/dev/null 2>/dev/null; then
  # Bucket does not exist, create it
  echo "Creating bucket $SETUPBUCKET..."
  aws s3 mb s3://$SETUPBUCKET --region $REGION
else
  echo "Bucket $SETUPBUCKET already exists, using the bucket"
fi

# update the boto3 layer into s3
echo "Updating boto3 layer into s3..."
aws s3 cp ./boto3-layer.zip s3://$SETUPBUCKET/boto3-layer.zip

# Export bucket name as environment variable
export EVAL_PIPELINE_SETUPBUCKET=$SETUPBUCKET


# sam build
echo "sam build..."
sam build

# sam package
echo "sam package..."
sam package --s3-bucket $SETUPBUCKET --output-template-file packaged.yaml --region $REGION

# sam deploy
echo "sam deploy..."
sam deploy --template-file packaged.yaml --stack-name llm-evaluation-stack --capabilities CAPABILITY_NAMED_IAM --parameter-overrides TrainingURL=763104351884.dkr.ecr.$REGION.amazonaws.com/pytorch-training:2.1.0-cpu-py310 --region $REGION

# Get the approximate number of items in the table
ITEM_COUNT=$(aws dynamodb describe-table --table-name SolutionTableDDB | jq .Table.ItemCount)

# Check if table is empty
if [ "$ITEM_COUNT" -eq "0" ]; then
  echo "Table SolutionTableDDB is empty... ingesting data"
  aws dynamodb batch-write-item --request-items file://data.json
else
  echo "Table SolutionTableDDB already contains $ITEM_COUNT items"
fi

APPLICATION_BUCKET="llm-evaluation-$ACCOUNT_ID-$REGION"
# check if an object exists in the bucket
if aws s3api head-object --bucket $APPLICATION_BUCKET --key questions/evaluation_questions_50.csv 1>/dev/null 2>/dev/null; then
    echo "files are in bucket, no need to copy"
else
    echo "evaluation_questions_50.csv does not exist in $APPLICATION_BUCKET, uploading it..."
    aws s3 cp ../evaluation_artifacts/evaluation_questions_50.csv s3://$APPLICATION_BUCKET/questions/evaluation_questions_50.csv
fi
