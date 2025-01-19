"""Constant values used for tests."""

from pathlib import Path

from aws_python.main import S3_BUCKET_NAME as TEST_BUCKET_NAME  # noqa: F401

THIS_DIR = Path(__file__).parent
PROJECT_DIR = (THIS_DIR / "../").resolve()
