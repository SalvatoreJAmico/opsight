# modules/api/errors.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("opsight.api")


def register_error_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(
            "Validation error",
            extra={
                "event": "request_validation_error",
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid request",
                "detail": exc.errors()
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(
            "HTTP error",
            extra={
                "event": "http_error",
                "path": request.url.path,
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Request failed",
                "detail": exc.detail
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled error",
            extra={
                "event": "unhandled_error",
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc)
            },
        )