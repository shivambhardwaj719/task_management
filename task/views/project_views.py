from task.services.project_service import ProjectService
from django.views.decorators.http import require_http_methods
from task.utils.response.handlers import (
    success_response,
    bad_request_response,
    unauthorized_response,
    forbidden_response,
    not_found_response,
)
from task.utils.response.messages import ResponseMessages
from task.utils.helpers import parse_json_body



@require_http_methods(["GET", "POST"])
def api_projects(request):
    if not request.user.is_authenticated:
        return unauthorized_response()

    if request.method == "GET":
        projects = ProjectService.list_projects_for_user(request.user)
        return success_response(data=projects, message=ResponseMessages.SUCCESS)

    elif request.method == "POST":
        data = parse_json_body(request)
        if data is None:
            return bad_request_response(message=ResponseMessages.INVALID_REQUEST)

        name = data.get("name", "")
        description = data.get("description", "")
        success, msg, detail_msg, project_data = ProjectService.create_project(
            name, description, request.user
        )
        if success:
            return success_response(data=project_data, message=msg, status_code=201)
        return bad_request_response(message=detail_msg)


@require_http_methods(["GET", "PUT", "DELETE"])
def api_project_detail(request, project_id):
    if not request.user.is_authenticated:
        return unauthorized_response()

    if request.method == "GET":
        success, msg, detail_msg, project_data = ProjectService.get_project_by_id(project_id, request.user)
        if success:
            return success_response(data=project_data, message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        return forbidden_response(message=detail_msg)

    elif request.method == "PUT":
        data = parse_json_body(request)
        if data is None:
            return bad_request_response(message=ResponseMessages.INVALID_REQUEST)

        name = data.get("name")
        description = data.get("description")
        success, msg, detail_msg, project_data = ProjectService.update_project(
            project_id, name, description, request.user
        )
        if success:
            return success_response(data=project_data, message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)

    elif request.method == "DELETE":
        success, msg, detail_msg = ProjectService.delete_project(project_id, request.user)
        if success:
            return success_response(message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)


@require_http_methods(["GET"])
def api_project_status_counts(request, project_id):
    if not request.user.is_authenticated:
        return unauthorized_response()

    success, msg, detail_msg, counts_data = ProjectService.get_per_project_status_counts(
        project_id, request.user
    )
    if success:
        return success_response(data=counts_data, message=msg)
    if msg == ResponseMessages.NOT_FOUND:
        return not_found_response(message=detail_msg)
    return forbidden_response(message=detail_msg)

