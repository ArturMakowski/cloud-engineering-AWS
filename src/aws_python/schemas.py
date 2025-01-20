"""Request and response schemas for the AWS Python API."""

from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)
from typing_extensions import Self

DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 100
DEFAULT_GET_FILES_DIRECTORY = ""


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

    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    )
    directory: str = DEFAULT_GET_FILES_DIRECTORY
    page_token: Optional[str] = None

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        """Ensure that page_token is mutually exclusive with page_size and directory."""
        if self.page_token:
            get_files_query_params: dict = self.model_dump(exclude_unset=True)
            page_size_set = "page_size" in get_files_query_params.keys()
            directory_set = "directory" in get_files_query_params.keys()
            if page_size_set or directory_set:
                raise ValueError(
                    "page_token is mutually exclusive with page_size and directory"
                )
        return self


class DeleteFileResponse(BaseModel):
    """Response for deleting a file."""

    message: str
