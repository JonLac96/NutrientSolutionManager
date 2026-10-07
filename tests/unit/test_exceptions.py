import pytest
from app.core.exceptions import (
    ConflictError,
    JobStateError,
    NotFoundError,
    SafetyLimitExceeded,
    ValidationError,
)


@pytest.mark.parametrize(
    ("error_type", "status_code", "code"),
    [
        (NotFoundError, 404, "not_found"),
        (ConflictError, 409, "conflict"),
        (ValidationError, 422, "validation_error"),
        (SafetyLimitExceeded, 409, "safety_limit_exceeded"),
        (JobStateError, 409, "job_state_error"),
    ],
)
def test_error_classes_carry_status_and_code(
    error_type: type[Exception],
    status_code: int,
    code: str,
) -> None:
    error = error_type("Hinweis")
    assert isinstance(error, error_type)
    assert error.status_code == status_code
    assert error.code == code
    assert error.message == "Hinweis"
    assert error.details is None


def test_error_code_and_details_can_be_set() -> None:
    error = NotFoundError(
        "GrowthStage 42 existiert nicht.",
        code="growth_stage_not_found",
        details={"id": 42},
    )
    assert error.code == "growth_stage_not_found"
    assert error.details == {"id": 42}
