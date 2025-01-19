"""Unit tests for the FastAPI application."""

import botocore
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aws_python.main import create_app
from aws_python.settings import Settings
from tests.consts import TEST_BUCKET_NAME

# Constants for testing
TEST_FILE_PATH = "test.txt"
TEST_FILE_CONTENT = b"Hello, world!"
TEST_FILE_CONTENT_TYPE = "text/plain"


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws):
    settings = Settings(s3_bucket_name=TEST_BUCKET_NAME)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client


def test_upload_file(client: TestClient) -> None:
    """Assert that a file can be uploaded successfully."""
    response = client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT)},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "file_path": TEST_FILE_PATH,
        "message": f"File uploaded successfully to path: /{TEST_FILE_PATH}",
    }

    updated_content = b"updated content"
    response = client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, updated_content)},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "file_path": TEST_FILE_PATH,
        "message": f"File already exists at path: /{TEST_FILE_PATH}",
    }


def test_list_files_with_pagination(client: TestClient) -> None:
    """Assert that files can be listed with pagination."""
    for i in range(15):
        client.put(
            f"/files/file{i}.txt",
            files={"file": (f"file{i}.txt", TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
        )
    # List files with page size 10
    response = client.get("/files?page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 10
    assert "next_page_token" in data

    # Helper function to extract number from filename
    def get_file_number(file_metadata: dict[str, str]) -> int:
        """Extract the file number from the file path."""
        return int(file_metadata["file_path"].replace("file", "").replace(".txt", ""))

    sorted_files = sorted(
        client.get("/files?page_size=15").json()["files"], key=get_file_number
    )
    print(sorted_files)
    for i, file_metadata in enumerate(sorted_files):
        assert file_metadata["file_path"] == f"file{i}.txt"


def test_get_file_metadata(client: TestClient):
    """Assert that file metadata can be fetched."""
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.head(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    headers = response.headers
    assert headers["Content-Type"] == TEST_FILE_CONTENT_TYPE
    assert headers["Content-Length"] == str(len(TEST_FILE_CONTENT))
    assert "Last-Modified" in headers


def test_get_file(client: TestClient):
    """Assert that a file can be fetched."""
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.get(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    assert response.content == TEST_FILE_CONTENT


def test_delete_file(client: TestClient):
    """Assert that a file can be deleted."""
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.delete(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 204

    with pytest.raises(botocore.exceptions.ClientError):
        response = client.get(f"/files/{TEST_FILE_PATH}")
