"""Functions for writing objects from an S3 bucket--the "C" and "U" in CRUD."""

from typing import Optional

import boto3

try:
    from mypy_boto3_s3 import S3Client
except ImportError:
    ...


def upload_s3_object(
    bucket_name: str,
    object_key: str,
    file_content: bytes,
    content_type: Optional[str] = None,
    s3_client: Optional["S3Client"] = None,
) -> None:
    """
    Upload a file to an S3 bucket.

    Args:
        bucket_name (str): Bucket name.
        object_key (str): Object key.
        file_content (bytes): File content.
        content_type (Optional[str], optional): Content type in MIME format. Defaults to None.
        s3_client (Optional[&quot;S3Client&quot;], optional): S3 client. Defaults to None.
    """
    content_type = content_type or "application/octet-stream"
    s3_client = s3_client or boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=file_content,
        ContentType=content_type,
    )
