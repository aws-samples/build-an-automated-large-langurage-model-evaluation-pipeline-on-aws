import boto3
import sys
import zipfile
import os

# We need to provide the following values. Better use env var. Hard coded for testing purpose.
lib_bucket = os.environ.get('LIB_BUCKET')       # bucket name created in create_bucket.py
lib_file = os.environ.get('LIB_FILE')       # zip file name created in create_bucket.py

# variables
def prepare_environment():
    directory_to_extract_to = '/tmp'
    path_to_zip_file = directory_to_extract_to + '/' + lib_file

    # Download dependencies
    s3_client = boto3.client('s3')
    s3_client.download_file(lib_bucket, lib_file, path_to_zip_file)

    # Unzip dependencies
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(directory_to_extract_to)

    return directory_to_extract_to
