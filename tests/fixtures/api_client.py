"""API client fixture for FastAPI tests."""

import pytest
from fastapi.testclient import TestClient

from aws_python.main import create_app
from aws_python.settings import Settings
from tests.consts import TEST_BUCKET_NAME


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws, mocked_openai):
    """Create a FastAPI test client."""
    settings = Settings(s3_bucket_name=TEST_BUCKET_NAME)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client
