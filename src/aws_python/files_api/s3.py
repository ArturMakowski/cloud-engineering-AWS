"""Upload a file to an S3 bucket."""

import os

import boto3
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BUCKET_NAME = "cloud-course-bucket-artur"

session = boto3.Session(profile_name=os.getenv("AWS_PROFILE_NAME"))
client = session.client(service_name="s3")

client.put_object(
    Bucket=BUCKET_NAME,
    Key="folder/file.txt",
    Body="Hello, World!",
    ContentType="text/plain",
)
