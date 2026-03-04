from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.logging import get_logger

logger = get_logger(__name__)


class BankingException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "BANKING_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class ResourceNotFoundError(BankingException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class InsufficientFundsError(BankingException):
    def __init__(self):
        super().__init__(
            message="Insufficient funds",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INSUFFICIENT_FUNDS",
        )


class DuplicateIdempotencyKeyError(BankingException):
    def __init__(self):
        super().__init__(
            message="A transfer with this idempotency key already exists",
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_IDEMPOTENCY_KEY",
        )


class OwnershipError(BankingException):
    def __init__(self):
        super().__init__(
            message="You do not have access to this resource",
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
        )


class AccountInactiveError(BankingException):
    def __init__(self):
        super().__init__(
            message="Account is not active",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ACCOUNT_INACTIVE",
        )


class AccountHasFundsError(BankingException):
    def __init__(self):
        super().__init__(
            message="Cannot close an account with a non-zero balance",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ACCOUNT_HAS_FUNDS",
        )


class OptimisticLockError(BankingException):
    def __init__(self):
        super().__init__(
            message="Account was modified by another request. Please retry.",
            status_code=status.HTTP_409_CONFLICT,
            code="CONCURRENT_MODIFICATION",
        )


class InvalidCardStatusError(BankingException):
    def __init__(self, reason: str):
        super().__init__(
            message=reason,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_CARD_STATUS",
        )


def _error_body(code: str, message: str, details=None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


async def banking_exception_handler(request: Request, exc: BankingException) -> JSONResponse:
    logger.warning("banking_exception", code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Pydantic v2 stores the raw ValueError in ctx['error'] which is not JSON-serializable.
    # Extract only the human-readable location and message.
    details = [
        {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    logger.warning("validation_error", details=details)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body("VALIDATION_ERROR", "Invalid request data", details),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error_type=type(exc).__name__, error_message=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body("INTERNAL_SERVER_ERROR", "An unexpected error occurred"),
    )
