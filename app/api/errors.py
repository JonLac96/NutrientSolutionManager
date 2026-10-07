import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import NsmError

logger = logging.getLogger(__name__)


def error_payload(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


def validation_fields(exc: RequestValidationError) -> list[str]:
    fields: list[str] = []
    for error in exc.errors():
        parts = [str(part) for part in error["loc"] if part != "body"]
        fields.append(".".join(parts) if parts else "body")
    return fields


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NsmError)
    async def handle_nsm_error(_request: Request, exc: NsmError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload(
                "validation_error",
                "Validierung fehlgeschlagen.",
                validation_fields(exc),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unerwarteter Fehler", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_payload("internal_error", "Unerwarteter Fehler."),
        )
