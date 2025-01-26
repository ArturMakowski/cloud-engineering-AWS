"""Unit tests for the FastAPI application."""

from fastapi import status
from fastapi.testclient import TestClient

from aws_python.schemas import GeneratedFileType

# Constants for testing
TEST_FILE_PATH = "test.txt"
TEST_FILE_CONTENT = b"Hello, world!"
TEST_FILE_CONTENT_TYPE = "text/plain"


def test_upload_file(client: TestClient) -> None:
    """Assert that a file can be uploaded successfully."""
    response = client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT)},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "file_path": TEST_FILE_PATH,
        "message": f"File uploaded successfully to path: /{TEST_FILE_PATH}",
    }

    updated_content = b"updated content"
    response = client.put(
        f"/v1/files/{TEST_FILE_PATH}",
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
            f"/v1/files/file{i}.txt",
            files={"file": (f"file{i}.txt", TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
        )
    # List files with page size 10
    response = client.get("/v1/files?page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 10
    assert "next_page_token" in data

    # Helper function to extract number from filename
    def get_file_number(file_metadata: dict[str, str]) -> int:
        """Extract the file number from the file path."""
        return int(file_metadata["file_path"].replace("file", "").replace(".txt", ""))

    sorted_files = sorted(
        client.get("/v1/files?page_size=15").json()["files"], key=get_file_number
    )
    print(sorted_files)
    for i, file_metadata in enumerate(sorted_files):
        assert file_metadata["file_path"] == f"file{i}.txt"


def test_get_file_metadata(client: TestClient):
    """Assert that file metadata can be fetched."""
    client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.head(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    headers = response.headers
    assert headers["Content-Type"] == TEST_FILE_CONTENT_TYPE
    assert headers["Content-Length"] == str(len(TEST_FILE_CONTENT))
    assert "Last-Modified" in headers


def test_get_file(client: TestClient):
    """Assert that a file can be fetched."""
    client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.get(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    assert response.content == TEST_FILE_CONTENT


def test_delete_file(client: TestClient):
    """Assert that a file can be deleted."""
    client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    response = client.delete(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_text(client: TestClient):
    """Test generating text using POST method."""
    response = client.post(
        url=f"/v1/files/generated/{TEST_FILE_PATH}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.TEXT.value},
    )

    respone_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        respone_data["message"]
        == f"New {GeneratedFileType.TEXT.value} file generated and uploaded at path: {TEST_FILE_PATH}"
    )

    response = client.get(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.content
        == b"This is a mock response from the chat completion endpoint."
    )
    assert "text/plain" in response.headers["Content-Type"]


def test_generate_image(client: TestClient):
    """Test generating image using POST method."""
    IMAGE_FILE_PATH = "some/nested/path/image.png"
    response = client.post(
        url=f"/v1/files/generated/{IMAGE_FILE_PATH}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.IMAGE.value},
    )

    respone_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        respone_data["message"]
        == f"New {GeneratedFileType.IMAGE.value} file generated and uploaded at path: {IMAGE_FILE_PATH}"
    )

    response = client.get(f"/v1/files/{IMAGE_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content is not None
    assert response.headers["Content-Type"] in ["image/png", "image/jpeg"]


def test_generate_audio(client: TestClient):
    """Test generating an audio file using the POST method."""
    audio_file_path = "some-audio.mp3"
    response = client.post(
        url=f"/v1/files/generated/{audio_file_path}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.AUDIO.value},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["message"] == (
        f"New text-to-speech file generated and uploaded at path: {audio_file_path}"
    )

    response = client.get(f"/v1/files/{audio_file_path}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content is not None
    assert response.headers["Content-Type"] == "audio/mpeg"
