"""Functions for reading objects from an S3 bucket--the "R" in CRUD."""

from typing import Optional

import boto3
from botocore.exceptions import ClientError

try:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import (
        GetObjectOutputTypeDef,
        ListObjectsV2OutputTypeDef,
        ObjectTypeDef,
    )
except ImportError:
    ...

DEFAULT_MAX_KEYS = 1_000


def object_exists_in_s3(
    bucket_name: str, object_key: str, s3_client: Optional["S3Client"] = None
) -> bool:
    """
    Check if an object exists in the S3 bucket using head_object.

    Args:
        bucket_name (str): Name of the S3 bucket.
        object_key (str): Key of the object to check.
        s3_client (Optional[S3Client]): Optional S3 client to use. If not provided, a new client will be created.

    Returns:
        bool: True if the object exists, False otherwise.
    """
    s3_client = s3_client or boto3.client("s3")
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def fetch_s3_object(
    bucket_name: str,
    object_key: str,
    s3_client: Optional["S3Client"] = None,
) -> "GetObjectOutputTypeDef":
    """
    Fetch metadata of an object in the S3 bucket.

    Args:
        bucket_name (str): Name of the S3 bucket.
        object_key (str): Key of the object to fetch.
        s3_client (Optional[S3Client]): Optional S3 client to use. If not provided, a new client will be created.

    Returns:
        GetObjectOutputTypeDef: Metadata of the object.
    """
    s3_client = s3_client or boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    return response


def fetch_s3_objects_using_page_token(
    bucket_name: str,
    continuation_token: str,
    max_keys: int | None = None,
    s3_client: Optional["S3Client"] = None,
) -> tuple[list["ObjectTypeDef"], Optional[str]]:
    """
    Fetch list of object keys and their metadata using a continuation token.

    Args:
        bucket_name (str): Name of the S3 bucket to list objects from.
        continuation_token (str): Token for fetching the next page of results where the last page left off.
        max_keys (int | None): Maximum number of keys to return within this page.
        s3_client (Optional[S3Client]): Optional S3 client to use. If not provided, a new client will be created.

    Returns:
        tuple[list[ObjectTypeDef], Optional[str]]: Tuple of a list of objects and the next continuation token.
            1. Possibly empty list of objects in the current page.
            2. Next continuation token if there are more pages, otherwise None.
    """
    s3_client = s3_client or boto3.client("s3")
    response: "ListObjectsV2OutputTypeDef" = s3_client.list_objects_v2(
        Bucket=bucket_name,
        ContinuationToken=continuation_token,
        MaxKeys=max_keys or DEFAULT_MAX_KEYS,
    )
    files: list["ObjectTypeDef"] = response.get("Contents", [])
    next_continuation_token: str | None = response.get("NextContinuationToken")

    return files, next_continuation_token


def fetch_s3_objects_metadata(
    bucket_name: str,
    prefix: Optional[str] = None,
    max_keys: Optional[int] = DEFAULT_MAX_KEYS,
    s3_client: Optional["S3Client"] = None,
) -> tuple[list["ObjectTypeDef"], Optional[str]]:
    """
    Fetch list of object keys and their metadata.

    Args:
        bucket_name (str): Name of the S3 bucket to list objects from.
        prefix (Optional[str]): Prefix to filter objects by.
        max_keys (Optional[int]): Maximum number of keys to return within this page.
        s3_client (Optional[S3Client]): Optional S3 client to use. If not provided, a new client will be created.

    Returns:
        tuple[list[ObjectTypeDef], Optional[str]]: Tuple of a list of objects and the next continuation token.
            1. Possibly empty list of objects in the current page.
            2. Next continuation token if there are more pages, otherwise None.
    """
    s3_client = s3_client or boto3.client("s3")
    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix or "", MaxKeys=max_keys
    )
    files: list["ObjectTypeDef"] = response.get("Contents", [])
    next_page_token: str | None = response.get("NextContinuationToken")

    return files, next_page_token
