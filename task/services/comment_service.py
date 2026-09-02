from task.models import Task, Comment
from task.services.project_service import ProjectService
from task.utils.response.messages import ResponseMessages


class CommentService:
    @staticmethod
    def list_comments_for_task(task_id: int, user):
        try:
            task = Task.objects.select_related('project').get(id=task_id)
        except Task.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Task not found", None

        if not ProjectService.is_member(task.project, user):
            return False, ResponseMessages.FORBIDDEN, "Access denied to task's project", None

        comments = Comment.objects.filter(task_id=task_id).select_related('author').order_by('created_at')

        data = [
            {
                "id": c.id,
                "task_id": c.task_id,
                "author_id": c.author_id,
                "author_username": c.author.username,
                "body": c.body,
                "created_at": c.created_at.isoformat()
            }
            for c in comments
        ]
        return True, ResponseMessages.SUCCESS, "Comments retrieved", data

    @staticmethod
    def add_comment(task_id: int, body: str, author_user):
        if not body or not body.strip():
            return False, ResponseMessages.VALIDATION_ERROR, "Comment body cannot be empty", None

        try:
            task = Task.objects.select_related('project').get(id=task_id)
        except Task.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Task not found", None

        if not ProjectService.is_member(task.project, author_user):
            return False, ResponseMessages.FORBIDDEN, "Access denied to task's project", None

        comment = Comment.objects.create(
            task=task,
            author=author_user,
            body=body.strip()
        )

        data = {
            "id": comment.id,
            "task_id": comment.task_id,
            "author_id": comment.author_id,
            "author_username": author_user.username,
            "body": comment.body,
            "created_at": comment.created_at.isoformat()
        }
        return True, ResponseMessages.COMMENT_ADDED, "Comment added successfully", data
