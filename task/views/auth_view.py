import json
from services.auth_service import AuthService
from django.views.decorators.http import require_http_methods
from utils.response.handlers import (
    success_response,
    bad_request_response,
    unauthorized_response,
)

from utils.response.messages import ResponseMessages


def parse_json_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return None
    return {}

@require_http_methods(["POST"])
def api_register(request):
    data = parse_json_body(request)
    if data is None:
        return bad_request_response(message=ResponseMessages.INVALID_REQUEST)

    username = data.get("username", "")
    password = data.get("password", "")
    email = data.get("email", "")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    success, msg, res_data = AuthService.register_user(
        request, username, password, email, first_name, last_name
    )
    if success:
        return success_response(data=res_data, message=msg, status_code=201)
    elif msg == ResponseMessages.BAD_REQUEST:
        return bad_request_response(message=res_data)
    else:
        return bad_request_response(message=res_data or msg)


@require_http_methods(["POST"])
def api_login(request):
    data = parse_json_body(request)
    if data is None:
        return bad_request_response(message=ResponseMessages.INVALID_REQUEST)

    username = data.get("username", "")
    password = data.get("password", "")

    success, msg, res_data = AuthService.login_user(request, username, password)
    if success:
        return success_response(data=res_data, message=msg)
    elif msg == ResponseMessages.UNAUTHORIZED:
        return unauthorized_response(message=res_data)
    else:
        return bad_request_response(message=res_data or msg)


@require_http_methods(["POST"])
def api_logout(request):
    if not request.user.is_authenticated:
        return unauthorized_response()
    success, msg, _ = AuthService.logout_user(request)
    return success_response(message=msg)


@require_http_methods(["GET"])
def api_me(request):
    success, msg, res_data = AuthService.get_current_user_data(request.user)
    if success:
        return success_response(data=res_data, message=msg)
    return unauthorized_response(message=msg)


@require_http_methods(["GET"])
def api_users(request):
    if not request.user.is_authenticated:
        return unauthorized_response()
    users = AuthService.list_all_users()
    return success_response(data=users, message=ResponseMessages.SUCCESS)