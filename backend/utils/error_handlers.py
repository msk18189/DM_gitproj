"""Centralized FastAPI exception handlers — no stack traces or secrets to clients."""
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.logging_config import get_logger
from utils.exceptions import GitHubPRDashboardException, InvalidURLError, ValidationError

logger = get_logger("error_handlers")


def _json_error(message: str, status_code: int, **extra) -> JSONResponse:
    body = {"success": False, "error": message, **extra}
    return JSONResponse(status_code=status_code, content=body)


async def dashboard_exception_handler(
    request: Request, exc: GitHubPRDashboardException
) -> JSONResponse:
    logger.info(
        "API error [%s] %s — %s",
        exc.status_code,
        request.url.path,
        exc.internal_details,
    )
    extra = {}
    if exc.status_code == 200:
        extra["success"] = True
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": exc.status_code < 400,
            "error": exc.user_message if exc.status_code >= 400 else None,
            "message": exc.user_message,
            **extra,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.info("Validation error on %s", request.url.path)
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "Invalid request")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return _json_error("; ".join(messages) or "Invalid request", 422)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, list):
        detail = "; ".join(
            str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail
        )
    elif not isinstance(detail, str):
        detail = str(detail)
    logger.info("HTTP %s on %s: %s", exc.status_code, request.url.path, detail)
    return _json_error(detail, exc.status_code)


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.info("ValueError on %s: %s", request.url.path, str(exc))
    return _json_error(str(exc), 400)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s: %s", request.url.path, type(exc).__name__, exc_info=True)
    msg = str(exc).lower()
    if any(k in msg for k in ("sqlalchemy", "psycopg", "asyncpg", "sqlite", "database")):
        return _json_error(
            "A data service error occurred. Please try again later.",
            500,
        )
    if isinstance(exc, ImportError):
        return _json_error("A required component is unavailable on the server.", 503)
    return _json_error(
        "An internal server error occurred. Please try again later.",
        500,
    )
