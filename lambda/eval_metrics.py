import json
import boto3
import os
import time
import logging
from botocore.exceptions import ClientError
import tarfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sm_client = boto3.client("sagemaker")
s3 = boto3.client('s3')

def name_from_base(base, max_length=63):
    """Append a timestamp to the provided string.

    This function assures that the total length of the resulting string is
    not longer than the specified max length, trimming the input parameter if
    necessary.

    Args:
        base (str): String used as prefix to generate the unique name.
        max_length (int): Maximum length for the resulting string (default: 63).
        short (bool): Whether or not to use a truncated timestamp (default: False).

    Returns:
        str: Input parameter with appended timestamp.
    """
    moment = time.time()
    moment_ms = repr(moment).split(".")[1][:3]

    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S-{}".format(moment_ms), time.gmtime(moment))
    trimmed_base = base[: max_length - len(timestamp) - 1]
    return "{}-{}".format(trimmed_base, timestamp)
    
def create_tarball(source_folder, tarball_name):
    tarball_path = f"/tmp/{tarball_name}"
    with tarfile.open(tarball_path, "w:gz") as tar:
        # Change the working directory to the source folder
        original_dir = os.getcwd()
        os.chdir(source_folder)

        # Add each file in the folder to the tarball
        for file in os.listdir():
            if os.path.isfile(file):
                tar.add(file)

        # Change back to the original directory
        os.chdir(original_dir)

    return tarball_path

def lambda_handler(event, context):
    logger.info(f"receiving event {event}")

    bucket = os.getenv("Bucket")
    prefix = os.getenv("MetricPrefix")
    image_uri = os.getenv("TrainingURL")
    role = os.getenv('SagemakerRoleArn')

    ## define the parameters
    input_data = event['evaluation_location']
    eval_output = f"s3://{bucket}/{prefix}/output"
    processing_job_name = name_from_base("llm-eval-metrics")
    instance_type = event['instance_type']
    metric = event['metric']
    data_file = input_data.split('/')[-1]
    
    # prepare resources, upload to s3
    sourcefile = "sourcedir.tar.gz"
    runfile = 'runproc.sh'
    folder_path = 'src'
    
    sourcedir = f"s3://{bucket}/{prefix}/source/{sourcefile}"
    entrypoint = f"s3://{bucket}/{prefix}/source/{runfile}"
    object_key = f'{prefix}/source/{runfile}'
    
    # upload run file
    try:
        s3.upload_file(f"{folder_path}/{runfile}", bucket, object_key)
    except ClientError as e:
        logger.info(f"Error occurred {e}")
        return None
    
    # prepare tarball and upload to s3
    tarball_path = create_tarball(folder_path, sourcefile)
    
    sourcefile_objectkey = f"{prefix}/source/{sourcefile}"
    try:
        s3.upload_file(tarball_path, bucket, sourcefile_objectkey)
    except ClientError as e:
        logger.info(f"Error occurred {e}")
        return None
    
    ## create processing job
    response = sm_client.create_processing_job(
        ProcessingInputs=[
            {
                "InputName": "input-1",
                "AppManaged": False,
                "S3Input": {
                    "S3Uri": input_data,
                    "LocalPath": "/opt/ml/processing/input/data",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File",
                    "S3DataDistributionType": "FullyReplicated",
                    "S3CompressionType": "None"
                }
            },
            {
                "InputName": "code",
                "AppManaged": False,
                "S3Input": {
                    "S3Uri": sourcedir,
                    "LocalPath": "/opt/ml/processing/input/code/",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File",
                    "S3DataDistributionType": "FullyReplicated",
                    "S3CompressionType": "None"
                }
            },
            {
                "InputName": "entrypoint",
                "AppManaged": False,
                "S3Input": {
                    "S3Uri": entrypoint,
                    "LocalPath": "/opt/ml/processing/input/entrypoint",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File",
                    "S3DataDistributionType": "FullyReplicated",
                    "S3CompressionType": "None"
                }
            }
        ],
        ProcessingOutputConfig={
            "Outputs": [
                {
                    "OutputName": "output",
                    "S3Output": {
                        "S3Uri": eval_output,
                        "LocalPath": "/opt/ml/processing/output",
                        "S3UploadMode": "EndOfJob"
                    },
                    "AppManaged": False
                }
            ]
        },
        ProcessingJobName=processing_job_name,
        ProcessingResources={
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": instance_type,
                "VolumeSizeInGB": 30
            }
        },
        AppSpecification={
            "ImageUri": image_uri,
            "ContainerEntrypoint": [
                "/bin/bash",
                "/opt/ml/processing/input/entrypoint/runproc.sh"
            ],
            "ContainerArguments": [
                "--base_dir",
                "/opt/ml/processing",
                "--metric",
                metric,
                "--data_file",
                data_file,
                "--bucket",
                bucket
            ]
        },
        RoleArn=role,
    )
    return {
        'statusCode': 200,
        'body': json.dumps(f'{response}')
    }
