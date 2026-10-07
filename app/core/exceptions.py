from typing import Any


class NsmError(Exception):
    status_code: int = 500
    code: str = "error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        if code is not None:
            self.code = code


class NotFoundError(NsmError):
    status_code = 404
    code = "not_found"


class ConflictError(NsmError):
    status_code = 409
    code = "conflict"


class ValidationError(NsmError):
    status_code = 422
    code = "validation_error"


class SafetyLimitExceeded(NsmError):
    status_code = 409
    code = "safety_limit_exceeded"


class JobStateError(NsmError):
    status_code = 409
    code = "job_state_error"
