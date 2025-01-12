"""Tests for the write_objects.py module."""

import boto3

from aws_python.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


def test__upload_s3_object(mocked_aws: None) -> None:
    """Test upload_s3_object."""
    object_key = "folder/file.txt"
    file_content = b"Hello, World!"
    content_type = "text/plain"

    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=object_key,
        file_content=file_content,
        content_type=content_type,
    )

    client = boto3.client(service_name="s3")
    response = client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_key)
    assert response["Body"].read() == file_content
    assert response["ContentType"] == content_type
