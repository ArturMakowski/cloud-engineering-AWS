"""Define the FastAPI routes for the AWS Python application."""

import mimetypes
from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from loguru import logger

from aws_python.generate_files import (
    generate_image,
    generate_text_to_speech,
    get_text_chat_completion,
)
from aws_python.s3.delete_objects import delete_s3_object
from aws_python.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from aws_python.s3.write_objects import upload_s3_object
from aws_python.schemas import (
    FileMetadata,
    GeneratedFileType,
    GenerateFilesQueryParams,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
    PutGeneratedFileResponse,
)
from aws_python.settings import Settings

ROUTER = APIRouter(tags=["Files"])
GENERATED_FILES_ROUTER = APIRouter(tags=["Generated Files"])


@ROUTER.put(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_200_OK: {"model": PutFileResponse},
        status.HTTP_201_CREATED: {"model": PutFileResponse},
    },
)
async def upload_file(
    request: Request, file_path: str, file: UploadFile, response: Response
) -> PutFileResponse:
    """Upload a file."""
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )

    if object_exists:
        response_message = f"File already exists at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"File uploaded successfully to path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_content: bytes = await file.read()
    logger.debug("file_content: {file_content}", file_content=file_content)
    upload_s3_object(
        bucket_name=settings.s3_bucket_name,
        object_key=file_path,
        file_content=file_content,
        content_type=file.content_type,
    )
    logger.info("response.status_code: {response.status_code}", response=response)
    logger.info(
        "response_message: {response_message}", response_message=response_message
    )
    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )


@ROUTER.get("/v1/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),  # noqa: B008
) -> GetFilesResponse:
    """List files with pagination."""
    settings: Settings = request.app.state.settings
    if query_params.page_token:
        files, next_page_token = fetch_s3_objects_using_page_token(
            bucket_name=settings.s3_bucket_name,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        files, next_page_token = fetch_s3_objects_metadata(
            bucket_name=settings.s3_bucket_name,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    logger.debug("query_params: {query_params}", query_params=query_params)
    file_metadata_objs = [
        FileMetadata(
            file_path=f"{item['Key']}",
            last_modified=item["LastModified"],
            size_bytes=item["Size"],
        )
        for item in files
    ]
    logger.debug(
        "file_metadata_objs: {file_metadata_objs}",
        file_metadata_objs=file_metadata_objs,
    )
    return GetFilesResponse(
        files=file_metadata_objs,
        next_page_token=next_page_token if next_page_token else None,
    )


@ROUTER.head(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "headers": {
                "Content-Type": {
                    "description": "The [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types) of the file.",
                    "example": "text/plain",
                    "schema": {"type": "string"},
                },
                "Content-Length": {
                    "description": "The size of the file in bytes.",
                    "example": 512,
                    "schema": {"type": "integer"},
                },
                "Last-Modified": {
                    "description": "The last modified date of the file.",
                    "example": "Thu, 01 Jan 2022 00:00:00 GMT",
                    "schema": {"type": "string", "format": "date-time"},
                },
            }
        },
    },
)
async def get_file_metadata(
    request: Request, file_path: str, response: Response
) -> Response:
    """Retrieve file metadata."""
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )
    if not object_exists:
        logger.error(
            "File not found for the given `file_path`: {file_path}", file_path=file_path
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    get_object_response = fetch_s3_object(settings.s3_bucket_name, object_key=file_path)
    logger.debug(
        "get_object_response: {get_object_response}",
        get_object_response=get_object_response,
    )
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK
    return response


@ROUTER.get(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "description": "The file content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
    },
)
async def get_file(
    request: Request,
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )

    if not object_exists:
        logger.error(
            "File not found for the given `file_path`: {file_path}", file_path=file_path
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    get_object_response = fetch_s3_object(settings.s3_bucket_name, object_key=file_path)
    return StreamingResponse(
        content=get_object_response["Body"],
        media_type=get_object_response["ContentType"],
    )


@ROUTER.delete(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_204_NO_CONTENT: {
            "description": "File deleted successfully.",
        },
    },
)
async def delete_file(
    request: Request,
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file."""
    settings: Settings = request.app.state.settings
    object_exists = object_exists_in_s3(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )

    if not object_exists:
        logger.error(
            "File not found for the given `file_path`: {file_path}", file_path=file_path
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    delete_s3_object(settings.s3_bucket_name, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@GENERATED_FILES_ROUTER.post(
    "/v1/files/generated/{file_path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="AI Generated Files",
    responses={
        status.HTTP_201_CREATED: {
            "model": PutGeneratedFileResponse,
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "text": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][0],
                        "image": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][1],
                        "text-to-speech": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][2],
                    },
                },
            },
        },
    },
)
async def generate_file_using_openai(
    request: Request,
    response: Response,
    query_params: Annotated[GenerateFilesQueryParams, Depends()],
) -> PutGeneratedFileResponse:
    """
    Generate a File using AI.

    Supported file types:
    - **text**: `.txt`
    - **image**: `.png`, `.jpg`, `.jpeg`
    - **text-to-speech**: `.mp3`, `.opus`, `.aac`, `.flac`, `.wav`, `.pcm`

    Note: the generated file type is derived from the file_path extension. So the file_path must have
    an extension matching one of the supported file types in the list above.
    """
    settings: Settings = request.app.state.settings
    s3_bucket_name = settings.s3_bucket_name

    # generate text
    if query_params.file_type == GeneratedFileType.TEXT:
        file_content = await get_text_chat_completion(prompt=query_params.prompt)
        file_content_bytes: bytes = file_content.encode(
            "utf-8"
        )  # convert string to bytes
        content_type = "text/plain"  # type: ignore

    # generate/download an image
    elif query_params.file_type == GeneratedFileType.IMAGE:
        image_url = await generate_image(prompt=query_params.prompt)
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url)
        file_content_bytes = image_response.content
        content_type = image_response.headers["Content-Type"]

    # generate audio
    else:
        response_audio_file_format = query_params.file_path.split(".")[
            -1
        ]  # the file extension
        file_content_bytes, content_type = await generate_text_to_speech(
            prompt=query_params.prompt,
            response_format=response_audio_file_format,  # type: ignore
        )

    # try to guess the mimetype from the file path's extension if we don't already know it
    content_type: str | None = (  # type: ignore
        content_type or mimetypes.guess_type(query_params.file_path)[0]
    )
    logger.debug("content_type: {content_type}", content_type=content_type)
    logger.debug("file_path: {file_path}", file_path=query_params.file_path)

    # Upload the generated file to S3
    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=query_params.file_path,
        file_content=file_content_bytes,
        content_type=content_type,
    )

    # return response
    response.status_code = status.HTTP_201_CREATED
    logger.info(
        "New {file_type} file generated and uploaded at path: {file_path}",
        file_type=query_params.file_type.value,
        file_path=query_params.file_path,
    )
    return PutGeneratedFileResponse(
        file_path=query_params.file_path,
        message=f"New {query_params.file_type.value} file generated and uploaded at path: {query_params.file_path}",
    )
