from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.exceptions.custom_exceptions import AppException
from app.exceptions.handlers import (
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routers.v1 import health, inventory

setup_logging()

if settings.is_production:
    docs_url = None
    redoc_url = None
    openapi_url = None
else:
    docs_url = "/inventory/docs"
    redoc_url = "/inventory/redoc"
    openapi_url = "/inventory/openapi.json"

app = FastAPI(
    title="Inventory Service",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.include_router(health.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
