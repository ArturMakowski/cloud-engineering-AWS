"""Main module for the FastAPI application."""

from textwrap import dedent

import pydantic
from fastapi import FastAPI
from fastapi.routing import APIRoute

from aws_python.errors import (
    handle_broad_exceptions,
    handle_pydantic_validation_errors,
)
from aws_python.monitoring.logger import inject_lambda_context__middleware
from aws_python.route_handler import RouteHandler
from aws_python.routes import GENERATED_FILES_ROUTER, ROUTER
from aws_python.settings import Settings


def custom_generate_unique_id(route: APIRoute):
    """
    Generate prettier `operationId`s in the OpenAPI schema.

    These become the function names in generated client SDKs.
    """
    return f"{route.tags[0]}-{route.name}"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a FastAPI application."""
    settings = settings or Settings()

    app = FastAPI(
        title="Files API",
        summary="Store and retrieve files.",
        version="v1",
        description=dedent("""Maintained by Armak."""),
        docs_url="/",  # its easier to find the docs when they live on the base url
        root_path="/prod",
        generate_unique_id_function=custom_generate_unique_id,
    )
    app.state.settings = settings

    app.router.route_class = RouteHandler
    app.include_router(ROUTER)
    app.include_router(GENERATED_FILES_ROUTER)

    app.add_exception_handler(
        exc_class_or_status_code=pydantic.ValidationError,
        handler=handle_pydantic_validation_errors,
    )
    app.middleware("http")(handle_broad_exceptions)
    app.middleware("http")(inject_lambda_context__middleware)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
