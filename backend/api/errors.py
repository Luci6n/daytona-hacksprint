from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.provider_errors import (
    ProviderConfigurationError,
    ProviderResponseError,
    UnsafeGuidanceError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        messages = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        detail = "; ".join(messages) or "Invalid request."
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ProviderConfigurationError)
    async def configuration_error_handler(
        _request: Request, exc: ProviderConfigurationError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(UnsafeGuidanceError)
    async def unsafe_guidance_handler(
        _request: Request, exc: UnsafeGuidanceError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ProviderResponseError)
    async def provider_response_handler(
        _request: Request, exc: ProviderResponseError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})
