from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from database.db import init_db
from config import CORS_ORIGINS, API_HOST, API_PORT, API_RELOAD
from utils.error_handlers import (
    dashboard_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from utils.exceptions import GitHubPRDashboardException
from utils.logging_config import get_logger
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = get_logger("main")

app = FastAPI(title="GitHub PR Intelligence Dashboard")

app.add_exception_handler(GitHubPRDashboardException, dashboard_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

try:
    init_db()
    logger.info("Database initialized")
except Exception as e:
    logger.warning("Database initialization issue: %s", e)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server on %s:%s", API_HOST, API_PORT)
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD)
