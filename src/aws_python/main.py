"""Main module for the FastAPI application."""

from fastapi import FastAPI

from aws_python.routes import ROUTER
from aws_python.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a FastAPI application."""
    settings = settings or Settings()

    app = FastAPI()
    app.state.settings = settings

    app.include_router(ROUTER)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
