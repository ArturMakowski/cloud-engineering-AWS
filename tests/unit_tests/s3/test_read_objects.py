"""Test cases for `s3.read_objects`."""

import boto3
import pytest
from botocore.exceptions import ClientError

from aws_python.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from tests.consts import TEST_BUCKET_NAME


def test_object_exists_in_s3(mocked_aws: None) -> None:
    """Assert that `object_exists_in_s3` returns the correct value when an object is or isn't present."""
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="testfile.txt", Body="test content"
    )
    assert object_exists_in_s3(TEST_BUCKET_NAME, "testfile.txt") is True
    assert object_exists_in_s3(TEST_BUCKET_NAME, "nonexistent.txt") is False


def test_pagination(mocked_aws: None) -> None:
    """Assert that pagination works correctly."""
    s3_client = boto3.client("s3")
    for i in range(1, 6):
        s3_client.put_object(
            Bucket=TEST_BUCKET_NAME, Key=f"file{i}.txt", Body=f"content {i}"
        )

    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=2)
    assert len(files) == 2
    assert files[0]["Key"] == "file1.txt"
    assert files[1]["Key"] == "file2.txt"

    files, next_page_token = fetch_s3_objects_using_page_token(
        TEST_BUCKET_NAME, next_page_token, max_keys=2
    )
    assert len(files) == 2
    assert files[0]["Key"] == "file3.txt"
    assert files[1]["Key"] == "file4.txt"

    files, next_page_token = fetch_s3_objects_using_page_token(
        TEST_BUCKET_NAME, next_page_token, max_keys=2
    )
    assert len(files) == 1
    assert files[0]["Key"] == "file5.txt"
    assert next_page_token is None


def test_mixed_page_sizes(mocked_aws: None) -> None:
    """Assert that pagination works correctly for pages of differing sizes."""
    s3_client = boto3.client("s3")
    for i in [1, 2, 3, 4, 5]:
        s3_client.put_object(
            Bucket=TEST_BUCKET_NAME, Key=f"file{i}.txt", Body=f"content {i}"
        )

    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=3)
    assert len(files) == 3
    assert files[0]["Key"] == "file1.txt"
    assert files[1]["Key"] == "file2.txt"
    assert files[2]["Key"] == "file3.txt"

    files, next_page_token = fetch_s3_objects_using_page_token(
        TEST_BUCKET_NAME, next_page_token, max_keys=1
    )
    assert len(files) == 1
    assert files[0]["Key"] == "file4.txt"

    files, next_page_token = fetch_s3_objects_using_page_token(
        TEST_BUCKET_NAME, next_page_token, max_keys=2
    )
    assert len(files) == 1
    assert files[0]["Key"] == "file5.txt"
    assert next_page_token is None


def test_directory_queries(mocked_aws: None) -> None:
    """Assert that queries with prefixes work correctly with various directory prefixes on object keys."""
    s3_client = boto3.client("s3")

    # Create objects
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="folder1/file1.txt", Body="content 1"
    )
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="folder1/file2.txt", Body="content 2"
    )
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="folder2/file3.txt", Body="content 3"
    )
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="folder2/subfolder1/file4.txt", Body="content 4"
    )
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="file5.txt", Body="content 5")

    # Query with prefix
    files, next_page_token = fetch_s3_objects_metadata(
        TEST_BUCKET_NAME, prefix="folder1/"
    )
    assert len(files) == 2
    assert files[0]["Key"] == "folder1/file1.txt"
    assert files[1]["Key"] == "folder1/file2.txt"
    assert next_page_token is None

    # Query with prefix for nested folder
    files, next_page_token = fetch_s3_objects_metadata(
        TEST_BUCKET_NAME, prefix="folder2/subfolder1/"
    )
    assert len(files) == 1
    assert files[0]["Key"] == "folder2/subfolder1/file4.txt"
    assert next_page_token is None

    # Query with no prefix
    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME)
    assert len(files) == 5
    assert files[0]["Key"] == "file5.txt"
    assert files[1]["Key"] == "folder1/file1.txt"
    assert files[2]["Key"] == "folder1/file2.txt"
    assert files[3]["Key"] == "folder2/file3.txt"
    assert files[4]["Key"] == "folder2/subfolder1/file4.txt"
    assert next_page_token is None


def test_fetch_s3_object(mocked_aws: None) -> None:
    """Assert that `fetch_s3_object` returns the correct metadata for an existing object."""
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=TEST_BUCKET_NAME, Key="testfile.txt", Body="test content"
    )

    response = fetch_s3_object(TEST_BUCKET_NAME, "testfile.txt")
    assert response["ContentLength"] == len("test content")
    assert response["ContentType"] == "binary/octet-stream"
    assert response["Body"].read().decode() == "test content"

    with pytest.raises(ClientError) as exc_info:
        fetch_s3_object(TEST_BUCKET_NAME, "nonexistent.txt")
    assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"


def test_object_exists_in_s3_raises_client_error(mocked_aws: None) -> None:
    """Assert that `object_exists_in_s3` raises ClientError for non-404 errors."""
    s3_client = boto3.client("s3")

    # Simulate a ClientError that is not a 404
    s3_client.head_object = lambda Bucket, Key: (_ for _ in ()).throw(
        ClientError(
            {"Error": {"Code": "500", "Message": "Internal Server Error"}},
            "HeadObject",
        )
    )

    with pytest.raises(ClientError) as exc_info:
        object_exists_in_s3(TEST_BUCKET_NAME, "testfile.txt", s3_client=s3_client)
    assert exc_info.value.response["Error"]["Code"] == "500"
