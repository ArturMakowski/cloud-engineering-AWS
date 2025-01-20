import os

import boto3
import botocore.exceptions
from loguru import logger
from moto import mock_aws
from pytest import fixture

from tests.consts import TEST_BUCKET_NAME
from tests.utils import delete_s3_bucket


def point_away_from_aws():
    """Point away from AWS."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"  # pragma: allowlist secret


@fixture
def mocked_aws():
    with mock_aws():
        logger.info("Pointing away from AWS...")
        point_away_from_aws()

        logger.info("Creating test bucket...")
        client = boto3.client(service_name="s3")
        client.create_bucket(Bucket=TEST_BUCKET_NAME)

        yield

        logger.info("Deleting test bucket...")
        try:
            delete_s3_bucket(TEST_BUCKET_NAME)
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchBucket":
                pass
            else:
                raise

        logger.info("Test bucket deleted.")
