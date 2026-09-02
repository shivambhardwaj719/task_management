from django.views.decorators.http import require_http_methods
from task.services.task_service import TaskService
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
def api_tasks(request):
    if not request.user.is_authenticated:
        return unauthorized_response()

    if request.method == "GET":
        project_id = request.GET.get("project_id")
        if not project_id:
            return bad_request_response(message="project_id query parameter is required")

        try:
            p_id = int(project_id)
        except ValueError:
            return bad_request_response(message="Invalid project_id parameter")

        success, msg, detail_msg, tasks = TaskService.list_tasks_for_project(p_id, request.user)
        if success:
            return success_response(data=tasks, message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        return forbidden_response(message=detail_msg)

    elif request.method == "POST":
        data = parse_json_body(request)
        if data is None:
            return bad_request_response(message="Invalid JSON payload")

        project_id = data.get("project_id")
        title = data.get("title", "")
        status = data.get("status", "TODO")
        priority = data.get("priority", "MEDIUM")
        due_date_str = data.get("due_date", "")
        assigned_to_id = data.get("assigned_to_id")

        if not project_id:
            return bad_request_response(message="project_id is required")

        success, msg, detail_msg, task_data = TaskService.create_task(
            project_id=project_id,
            title=title,
            status=status,
            priority=priority,
            due_date_str=due_date_str,
            assigned_to_id=assigned_to_id,
            user=request.user
        )
        if success:
            return success_response(data=task_data, message=msg, status_code=201)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)


@require_http_methods(["PUT", "DELETE"])
def api_task_detail(request, task_id):
    if not request.user.is_authenticated:
        return unauthorized_response()

    if request.method == "PUT":
        data = parse_json_body(request)
        if data is None:
            return bad_request_response(message="Invalid JSON payload")

        success, msg, detail_msg, task_data = TaskService.update_task(
            task_id=task_id,
            title=data.get("title"),
            status=data.get("status"),
            priority=data.get("priority"),
            due_date_str=data.get("due_date"),
            assigned_to_id=data.get("assigned_to_id"),
            user=request.user
        )
        if success:
            return success_response(data=task_data, message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)

    elif request.method == "DELETE":
        success, msg, detail_msg = TaskService.delete_task(task_id, request.user)
        if success:
            return success_response(message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)


@require_http_methods(["GET"])
def api_overdue_tasks(request):
    if not request.user.is_authenticated:
        return unauthorized_response()

    success, msg, detail_msg, tasks = TaskService.get_overdue_tasks(request.user)
    if success:
        return success_response(data=tasks, message=msg)
    return bad_request_response(message=detail_msg)