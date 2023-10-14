# How to use this repository to setup the evaluation pipelines

## prerequirsition

You need to have the following tools/settings to setup the pipeline
- git
- sam
- aws
- a s3 bucket you can upload artifacts

## step 1. clone the repository
command:
```bash
git clone https://github.com/aws-samples/build-an-automated-large-langurage-model-evaluation-pipeline-on-aws.git
```

## step 2. zip the code and upload to your bucket
commands:
```bash
cd build-an-automated-large-langurage-model-evaluation-pipeline-on-aws
zip -r code.zip *
aws s3 cp code.zip s3://<replace-with-your-bucket>
```

## setup 3. prevision the infrastructure with SAM/CloudFormation
commands:
```bash
cd infrastructure
sam build
sam package --output-template-file packaged.yaml --s3-bucket <replace-with-your-bucket>
sam deploy --template-file packaged.yaml --stack-name llm-evaluation-stack --capabilities CAPABILITY_IAM --parameter-overrides  pCodeBucket=<replace-with-your-bucket> pCodeKey=code.zip
```