from django.views.decorators.http import require_http_methods
from task.services.comment_service import CommentService
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
def api_task_comments(request, task_id):
    if not request.user.is_authenticated:
        return unauthorized_response()

    if request.method == "GET":
        success, msg, detail_msg, comments = CommentService.list_comments_for_task(task_id, request.user)
        if success:
            return success_response(data=comments, message=msg)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        return forbidden_response(message=detail_msg)

    elif request.method == "POST":
        data = parse_json_body(request)
        if data is None:
            return bad_request_response(message="Invalid JSON payload")

        body = data.get("body", "")
        success, msg, detail_msg, comment_data = CommentService.add_comment(
            task_id=task_id, body=body, author_user=request.user
        )
        if success:
            return success_response(data=comment_data, message=msg, status_code=201)
        if msg == ResponseMessages.NOT_FOUND:
            return not_found_response(message=detail_msg)
        if msg == ResponseMessages.FORBIDDEN:
            return forbidden_response(message=detail_msg)
        return bad_request_response(message=detail_msg)