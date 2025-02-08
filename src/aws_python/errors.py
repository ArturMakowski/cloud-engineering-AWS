"""Error handling middleware and exception handlers for FastAPI."""

import pydantic
from fastapi import (
    Request,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger

from aws_python.monitoring.logger import log_response_info


# fastapi docs on middlewares: https://fastapi.tiangolo.com/tutorial/middleware/
async def handle_broad_exceptions(request: Request, call_next):
    """Handle any exception that goes unhandled by a more specific exception handler."""
    try:
        return await call_next(request)
    except Exception as e:
        logger.opt(exception=e).error("HTTP_500_INTERNAL_SERVER_ERROR")
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
        log_response_info(response)
        return response


# fastapi docs on error handlers: https://fastapi.tiangolo.com/tutorial/handling-errors/
async def handle_pydantic_validation_errors(
    request: Request, exc: pydantic.ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.opt(exception=exc).error("HTTP_422_UNPROCESSABLE_ENTITY")
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": [
                {
                    "msg": error["msg"],
                    "input": error["input"],
                }
                for error in errors
            ]
        },
    )
    log_response_info(response)
    return response
