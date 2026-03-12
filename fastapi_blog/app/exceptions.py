from fastapi import Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="templates")


async def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = (
        exc.detail or "An error occurred. Please check your request and try again."
    )
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code, "title": exc.status_code, "message": message},
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": 422,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
