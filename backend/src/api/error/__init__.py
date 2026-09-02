from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiFailure(BaseModel):
    key: str
    message: str
    field: str | None = None


class ApiFailures(BaseModel):
    failures: list[ApiFailure]


class HttpApiFailure(HTTPException):
    def __init__(
        self,
        status_code: int,
        key: str,
        message: str,
        field: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.key: str = key
        self.field: str | None = field


ERROR_RESPONSE = {"model": ApiFailures}


def _build_json_response(status_code: int, failures: list[ApiFailure]) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=ApiFailures(failures=failures).model_dump()
    )


def request_validation_error_json(
    exception: RequestValidationError,
) -> JSONResponse:
    return _build_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        failures=[
            ApiFailure(
                key=error["type"],
                message=error["msg"],
                field=".".join(
                    str(loc)
                    for loc in error["loc"]
                    if loc not in ("body", "query", "path")
                )
                or None,
            )
            for error in exception.errors()
        ],
    )


def http_exception_json(exception: HTTPException) -> JSONResponse:
    return _build_json_response(
        status_code=exception.status_code,
        failures=[
            ApiFailure(
                key=getattr(exception, "key", f"http_{exception.status_code}"),
                message=exception.detail,
                field=getattr(exception, "field", None),
            )
        ],
    )


def unhandled_exception_json() -> JSONResponse:
    return _build_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        failures=[ApiFailure(key="internal_error", message="Internal server error")],
    )
