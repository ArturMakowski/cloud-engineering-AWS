"""Request and response schemas for the AWS Python API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
