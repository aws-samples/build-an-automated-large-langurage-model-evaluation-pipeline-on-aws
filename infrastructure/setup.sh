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

# Export bucket name as environment variable
export EVAL_PIPELINE_BUCKET=$BUCKET


# sam build
echo "sam build..."
sam build

# sam package
echo "sam package..."
sam package --s3-bucket $BUCKET --output-template-file packaged.yaml --region $REGION

# sam deploy
echo "sam deploy..."
sam deploy --template-file packaged.yaml --stack-name llm-evaluation-stack --capabilities CAPABILITY_NAMED_IAM --parameter-overrides TrainingURL=763104351884.dkr.ecr.$REGION.amazonaws.com/pytorch-training:2.1.0-cpu-py310 --region $REGION
