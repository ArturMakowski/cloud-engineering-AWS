from datetime import datetime
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aws_python.s3.delete_objects import delete_s3_object
from aws_python.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from aws_python.s3.write_objects import upload_s3_object

#####################
# --- Constants --- #
#####################

S3_BUCKET_NAME = "some-bucket"

APP = FastAPI()

####################################
# --- Request/response schemas --- #
####################################


class FileMetadata(BaseModel):
    """Metadata for a file."""

    file_path: str
    last_modified: datetime
    size_bytes: int


class PutFileResponse(BaseModel):
    """Response for uploading a file."""

    file_path: str
    message: str


class ListFilesResponse(BaseModel):
    """Response for listing files."""

    files: list[FileMetadata]


class GetFilesResponse(BaseModel):
    """Response for listing files with pagination."""

    files: list[FileMetadata]
    next_page_token: Optional[str]


class GetFilesQueryParams(BaseModel):
    """Query parameters for listing files."""

    page_size: int = 10
    directory: Optional[str] = ""
    page_token: Optional[str] = None


class DeleteFileResponse(BaseModel):
    """Response for deleting a file."""

    message: str


##################
# --- Routes --- #
##################


@APP.put("/files/{file_path:path}")
async def upload_file(
    file_path: str, file: UploadFile, response: Response
) -> PutFileResponse:
    """Upload a file."""
    object_exists = object_exists_in_s3(
        bucket_name=S3_BUCKET_NAME, object_key=file_path
    )

    if object_exists:
        response_message = f"File already exists at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"File uploaded successfully to path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_content: bytes = await file.read()
    upload_s3_object(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
        file_content=file_content,
        content_type=file.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )


@APP.get("/files")
async def list_files(
    query_params: GetFilesQueryParams = Depends(),  # noqa: B008
) -> GetFilesResponse:
    """List files with pagination."""
    if query_params.page_token:
        files, next_page_token = fetch_s3_objects_using_page_token(
            bucket_name=S3_BUCKET_NAME,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        files, next_page_token = fetch_s3_objects_metadata(
            bucket_name=S3_BUCKET_NAME,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    file_metadata_objs = [
        FileMetadata(
            file_path=f"{item['Key']}",
            last_modified=item["LastModified"],
            size_bytes=item["Size"],
        )
        for item in files
    ]
    return GetFilesResponse(
        files=file_metadata_objs,
        next_page_token=next_page_token if next_page_token else None,
    )


@APP.head("/files/{file_path:path}")
async def get_file_metadata(file_path: str, response: Response) -> Response:
    """Retrieve file metadata."""
    get_object_response = fetch_s3_object(S3_BUCKET_NAME, object_key=file_path)
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK
    return response


@APP.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    get_object_response = fetch_s3_object(S3_BUCKET_NAME, object_key=file_path)
    return StreamingResponse(
        content=get_object_response["Body"],
        media_type=get_object_response["ContentType"],
    )


@APP.delete("/files/{file_path:path}")
async def delete_file(
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file."""
    delete_s3_object(S3_BUCKET_NAME, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
