"""Request and response schemas for the AWS Python API."""

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
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

    file_path: str = Field(
        description="The path of the file.",
        json_schema_extra={"example": "path/to/pyproject.toml"},
    )
    last_modified: datetime = Field(description="The last modified date of the file.")
    size_bytes: int = Field(description="The size of the file in bytes.")


class PutFileResponse(BaseModel):
    """Response for uploading a file."""

    file_path: str = Field(
        description="The path of the file.",
        json_schema_extra={"example": "path/to/pyproject.toml"},
    )
    message: str = Field(description="A message about the operation.")


class ListFilesResponse(BaseModel):
    """Response for listing files."""

    files: list[FileMetadata]


class GetFilesResponse(BaseModel):
    """Response for listing files with pagination."""

    files: list[FileMetadata]
    next_page_token: Optional[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": [
                    {
                        "file_path": "path/to/pyproject.toml",
                        "last_modified": "2022-01-01T00:00:00Z",
                        "size_bytes": 512,
                    },
                    {
                        "file_path": "path/to/Makefile",
                        "last_modified": "2022-01-01T00:00:00Z",
                        "size_bytes": 256,
                    },
                ],
                "next_page_token": "next_page_token_example",
            }
        }
    )


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


class GeneratedFileType(str, Enum):
    """The type of file generated by OpenAI."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "text-to-speech"


class GenerateFilesQueryParams(BaseModel):
    """Query parameters for `POST /v1/files/generated`."""

    file_path: str = Field(
        ...,
        description="The path to the file to generate.",
        json_schema_extra={"example": "path/to/file.txt"},
        pattern=r"^.*\.(txt|png|jpg|jpeg|mp3|opus|aac|flac|wav|pcm)$",
    )
    prompt: str = Field(
        ...,
        description="The prompt to generate the file content.",
        json_schema_extra={"example": "Generate a text file."},
    )
    file_type: GeneratedFileType = Field(
        ...,
        description="The type of file to generate.",
        json_schema_extra={"example": "Text"},
    )

    @model_validator(mode="after")
    def validate_file_path_extension(self) -> Self:
        """Ensure that the file path extension matches the file type being generated."""
        file_type = self.file_type.value

        if file_type == GeneratedFileType.TEXT and not re.match(
            r".*\.txt$", self.file_path
        ):
            raise ValueError("For text files, the path must end with .txt")

        if file_type == GeneratedFileType.IMAGE and not re.match(
            r".*\.(png|jpg|jpeg)$", self.file_path
        ):
            raise ValueError(
                "For image files, the path must end with .png, .jpg, or .jpeg"
            )

        # these response formats are here: https://platform.openai.com/docs/api-reference/audio/createSpeech
        if file_type == GeneratedFileType.AUDIO and not re.match(
            r".*\.(mp3|opus|aac|flac|wav|pcm)$", self.file_path
        ):
            raise ValueError(
                "For audio files, the path must end with .mp3, .opus, .aac, .flac, .wav, or .pcm"
            )

        return self


class PutGeneratedFileResponse(BaseModel):
    """Response model for `POST /v1/files/generated/:file_path`."""

    file_path: str = Field(
        description="The path to the file.",
        json_schema_extra={"example": "path/to/file.txt"},
    )
    message: str = Field(
        description="The message indicating the status of the operation.",
        json_schema_extra={
            "example": "New file generated and uploaded at path: path/to/file.txt"
        },
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "value": {
                        "file_path": "path/to/file.txt",
                        "message": "New text file generated and uploaded at path: path/to/file.txt",
                    },
                },
                {
                    "value": {
                        "file_path": "path/to/image.png",
                        "message": "New image file generated and uploaded at path: path/to/image.png",
                    },
                },
                {
                    "value": {
                        "file_path": "path/to/speech.mp3",
                        "message": "New Text-to-Speech file generated and uploaded at path: path/to/speech.mp3",
                    },
                },
            ]
        }
    )
