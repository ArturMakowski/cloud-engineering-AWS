"""Test cases for `s3.delete_objects`."""

from aws_python.s3.delete_objects import delete_s3_object
from aws_python.s3.read_objects import object_exists_in_s3
from aws_python.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


def test_delete_existing_s3_object(mocked_aws: None) -> None:
    """Assert that `delete_s3_object` deletes an object from an S3 bucket."""
    upload_s3_object(TEST_BUCKET_NAME, "testfile.txt", b"test content")
    delete_s3_object(TEST_BUCKET_NAME, "testfile.txt")
    assert object_exists_in_s3(TEST_BUCKET_NAME, "testfile.txt") is False


def test_delete_nonexistent_s3_object(mocked_aws: None) -> None:
    """Assert that `delete_s3_object` does not raise an error when deleting a nonexistent object."""
    upload_s3_object(TEST_BUCKET_NAME, "nonexistent.txt", b"test content")
    delete_s3_object(TEST_BUCKET_NAME, "nonexistent.txt")
    delete_s3_object(TEST_BUCKET_NAME, "nonexistent.txt")
    assert object_exists_in_s3(TEST_BUCKET_NAME, "nonexistent.txt") is False
