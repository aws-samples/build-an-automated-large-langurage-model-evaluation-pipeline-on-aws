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
BUCKET="eval-$ACCOUNT_ID-$REGION"

# Check if bucket exists
if ! aws s3api head-bucket --bucket $BUCKET --region $REGION 1>/dev/null 2>/dev/null; then
  # Bucket does not exist, create it
  echo "Creating bucket $BUCKET..."
  aws s3 mb s3://$BUCKET --region $REGION
else
  echo "Bucket $BUCKET already exists, using the bucket"
fi

# update the boto3 layer into s3
echo "Updating boto3 layer into s3..."
aws s3 cp ./boto3-layer.zip s3://$BUCKET/boto3-layer.zip

# Export bucket name as environment variable
export EVAL_PIPELINE_BUCKET=$BUCKET

# create a ecr repository
echo "check if api-layer repository exists..."
aws ecr describe-repositories --repository-names api-layer --region $REGION 1>/dev/null 2>/dev/null
if [ $? -ne 0 ]; then
    echo "api-layer repository does not exist, creating..."
    aws ecr create-repository --repository-name api-layer --region $REGION
    echo "api-layer repository created"
fi

# build the api layer
echo "login to ecr..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
echo "building api layer..."
cd ../api-layer
docker build -t api-layer .
docker tag api-layer:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/api-layer:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/api-layer:latest
echo "api layer build completed"


# back to the setup folder
cd ../infrastructure

# sam build
echo "sam build..."
sam build

# sam package
echo "sam package..."
sam package --s3-bucket $BUCKET --output-template-file packaged.yaml --region $REGION

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

ITEM_COUNT=$(aws dynamodb describe-table --table-name SolutionTableDDB | jq .Table.ItemCount)

# Check if table is empty
if [ "$ITEM_COUNT" -eq "0" ]; then
  echo "Table SolutionTableDDB is empty... ingesting data"
  aws dynamodb batch-write-item --request-items file://solutionddb-data.json
else
  echo "Table SolutionTableDDB already contains $ITEM_COUNT items"
fi

ITEM_COUNT=$(aws dynamodb describe-table --table-name api-layer-ddb| jq .Table.ItemCount)

# Check if table is empty
if [ "$ITEM_COUNT" -eq "0" ]; then
  echo "Table api-layer-ddb is empty... ingesting data"
  aws dynamodb batch-write-item --request-items file://api-layer-ddb-data.json
else
  echo "Table SolutionTableDDB already contains $ITEM_COUNT items"
fi
