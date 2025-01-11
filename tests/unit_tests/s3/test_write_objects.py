"""Tests for the write_objects.py module."""

import os
import uuid

import boto3
from dotenv import find_dotenv, load_dotenv
from moto import mock_aws

from aws_python.s3.write_objects import upload_s3_object

load_dotenv(find_dotenv())

TEST_BUCKET_NAME = f"test-cloud-course-bucket-artur-{str(uuid.uuid4())[:5]}"


def point_away_from_aws():
    """Point away from AWS."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"  # pragma: allowlist secret


@mock_aws
def test__upload_s3_object():
    """Test upload_s3_object."""
    point_away_from_aws()

    client = boto3.client(service_name="s3")
    client.create_bucket(Bucket=TEST_BUCKET_NAME)

    object_key = "folder/file.txt"
    file_content = b"Hello, World!"
    content_type = "text/plain"

    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=object_key,
        file_content=file_content,
        content_type=content_type,
    )

    response = client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_key)
    assert response["Body"].read() == file_content
    assert response["ContentType"] == content_type

    response = client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
    for obj in response.get("Contents", []):
        client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj["Key"])
    client.delete_bucket(Bucket=TEST_BUCKET_NAME)
