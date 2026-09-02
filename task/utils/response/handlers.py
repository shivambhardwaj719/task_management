from typing import Any, Optional
import logging
from django.http import JsonResponse
from task.utils.response.messages import ResponseMessages, get_message

logger = logging.getLogger("task_management")


def success_response(
    data: Any = None,
    message: str = ResponseMessages.SUCCESS,
    status_code: int = 200,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": True,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def bad_request_response(
    data: Any = None,
    message: str = ResponseMessages.BAD_REQUEST,
    status_code: int = 400,
    errors: Any = None,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    content = {
        "success": False,
        "message": resolved_message,
        "data": data if data is not None else []
    }
    if errors is not None:
        content["errors"] = errors

    response = JsonResponse(content, status=status_code)
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def unauthorized_response(
    data: Any = None,
    message: str = ResponseMessages.UNAUTHORIZED,
    status_code: int = 401,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": False,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def forbidden_response(
    data: Any = None,
    message: str = ResponseMessages.FORBIDDEN,
    status_code: int = 403,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": False,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def not_found_response(
    data: Any = None,
    message: str = ResponseMessages.NOT_FOUND,
    status_code: int = 404,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": False,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def too_many_requests_response(
    data: Any = None,
    message: str = ResponseMessages.TOO_MANY_REQUESTS,
    status_code: int = 429,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": False,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def server_error_response(
    data: Any = None,
    message: str = ResponseMessages.SERVER_ERROR,
    status_code: int = 500,
    err: Optional[Exception] = None,
    headers: Optional[dict] = None
) -> JsonResponse:
    if err:
        logger.error(f"Server Error: {err}", exc_info=True)
    resolved_message = get_message(message, default=message)
    response = JsonResponse(
        {
            "success": False,
            "message": resolved_message,
            "data": data if data is not None else []
        },
        status=status_code
    )
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


def error_response(
    message: str = ResponseMessages.SERVER_ERROR,
    status_code: int = 400,
    errors: Any = None,
    headers: Optional[dict] = None
) -> JsonResponse:
    resolved_message = get_message(message, default=message)
    content = {
        "success": False,
        "message": resolved_message,
        "data": []
    }
    if errors is not None:
        content["errors"] = errors

    response = JsonResponse(content, status=status_code)
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response
