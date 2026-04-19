"""
Centralized exception handling.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import logger


class Note2MotionError(Exception):
    """Base domain exception."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PipelineError(Note2MotionError):
    pass


class ValidationFailedError(Note2MotionError):
    pass


class LLMError(Note2MotionError):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Note2MotionError)
    async def domain_error_handler(request: Request, exc: Note2MotionError):
        logger.warning(f"Domain error: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "message": "Something went wrong."},
        )