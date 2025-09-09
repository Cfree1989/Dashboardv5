import json
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode


def _as_json(response):
    # ResponseService returns (response, status)
    # response may be a Flask Response with .get_data or a test Response-like object with .json
    try:
        return response.json
    except Exception:
        return json.loads(response.get_data(as_text=True))


def test_standardized_error_and_success_formats():
    # 1) Validation Error
    response, status = ResponseService.validation_error(
        message="Invalid input provided",
        error_code=ErrorCode.INVALID_INPUT.value,
        field="email",
    )
    data = _as_json(response)
    assert status == 400
    assert data["error"]["code"] == ErrorCode.INVALID_INPUT.value
    assert data["error"]["category"] == ErrorCategory.VALIDATION.value
    assert data["error"]["field"] == "email"

    # 2) Not Found Error
    response, status = ResponseService.not_found(resource="User", error_code=ErrorCode.RESOURCE_NOT_FOUND.value)
    data = _as_json(response)
    assert status == 404
    assert data["error"]["message"] == "User not found"

    # 3) Server Error
    response, status = ResponseService.server_error(
        message="Database connection failed",
        error_code=ErrorCode.INTERNAL_SERVER_ERROR.value,
    )
    data = _as_json(response)
    assert status == 500
    assert data["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR.value

    # 4) Conflict Error
    response, status = ResponseService.conflict(
        message="Resource already exists",
        error_code=ErrorCode.RESOURCE_CONFLICT.value,
    )
    data = _as_json(response)
    assert status == 409
    assert data["error"]["code"] == ErrorCode.RESOURCE_CONFLICT.value

    # 5) Business Error
    response, status = ResponseService.business_error(
        message="Insufficient permissions",
        error_code=ErrorCode.BUSINESS_RULE_VIOLATION.value,
    )
    data = _as_json(response)
    assert status == 422
    assert data["error"]["code"] == ErrorCode.BUSINESS_RULE_VIOLATION.value

    # 6) File Operation Error
    response, status = ResponseService.file_operation_error(
        message="Failed to upload file",
        details={"file_size": "10MB", "max_size": "5MB"},
    )
    data = _as_json(response)
    assert status == 500
    assert data["error"]["code"] == ErrorCode.FILE_OPERATION_ERROR.value
    assert data["error"]["details"]["max_size"] == "5MB"

    # 7) Database Error
    response, status = ResponseService.database_error(
        message="Connection timeout",
        details={"operation": "INSERT", "table": "jobs"},
    )
    data = _as_json(response)
    assert status == 500
    assert data["error"]["code"] == ErrorCode.DATABASE_ERROR.value

    # 8) Success Response
    response, status = ResponseService.success(
        {
            "message": "Operation completed successfully",
            "data": {"id": 123, "status": "active"},
        }
    )
    data = _as_json(response)
    assert status == 200
    assert data["message"] == "Operation completed successfully"
    assert data["data"]["id"] == 123


