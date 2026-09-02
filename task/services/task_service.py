from datetime import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from task.models import Task, Project
from task.services.project_service import ProjectService
from task.utils.response.messages import ResponseMessages


class TaskService:
    @staticmethod
    def _format_task(task: Task) -> dict:
        today = timezone.now().date()
        is_overdue = (task.due_date < today) and (task.status != Task.Status.DONE)
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "status_display": task.get_status_display(),
            "priority": task.priority,
            "priority_display": task.get_priority_display(),
            "due_date": task.due_date.isoformat(),
            "is_overdue": is_overdue,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else "",
            "project_owner_id": task.project.owner_id if task.project else None,
            "assigned_to_id": task.assigned_to_id if task.assigned_to else None,
            "assigned_to_username": task.assigned_to.username if task.assigned_to else "Unassigned",
            "created_at": task.created_at.isoformat()
        }

    @staticmethod
    def list_tasks_for_project(project_id: int, user):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found", None

        if not ProjectService.is_member(project, user):
            return False, ResponseMessages.FORBIDDEN, "Access denied to this project", None

        tasks = (
            Task.objects.filter(project_id=project_id)
            .select_related('project', 'assigned_to')
            .order_by('due_date', '-priority')
        )
        task_list = [TaskService._format_task(t) for t in tasks]
        return True, ResponseMessages.SUCCESS, "Tasks retrieved", task_list

    @staticmethod
    def create_task(project_id: int, title: str, status: str, priority: str, due_date_str: str, assigned_to_id, user):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found", None

        if not ProjectService.is_owner(project, user):
            return False, ResponseMessages.FORBIDDEN, ResponseMessages.ONLY_OWNER_CAN_EDIT_TASK, None

        if not title or not title.strip():
            return False, ResponseMessages.VALIDATION_ERROR, "Task title is required", None

        if not due_date_str:
            return False, ResponseMessages.VALIDATION_ERROR, "Due date is required", None

        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, ResponseMessages.VALIDATION_ERROR, "Invalid due_date format (expected YYYY-MM-DD)", None

        assigned_user = None
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                return False, ResponseMessages.NOT_FOUND, "Assigned user not found", None

        valid_status = status if status in Task.Status.values else Task.Status.TODO
        valid_priority = priority if priority in Task.Priority.values else Task.Priority.MEDIUM

        task = Task.objects.create(
            title=title.strip(),
            status=valid_status,
            priority=valid_priority,
            due_date=due_date,
            project=project,
            assigned_to=assigned_user
        )
        task = Task.objects.select_related('project', 'assigned_to').get(id=task.id)
        return True, ResponseMessages.TASK_CREATED, "Task created successfully", TaskService._format_task(task)

    @staticmethod
    def update_task(task_id: int, title=None, status=None, priority=None, due_date_str=None, assigned_to_id=None, user=None):
        try:
            task = Task.objects.select_related('project', 'assigned_to').get(id=task_id)
        except Task.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Task not found", None

        if not ProjectService.is_owner(task.project, user):
            return False, ResponseMessages.FORBIDDEN, ResponseMessages.ONLY_OWNER_CAN_EDIT_TASK, None

        if title is not None and title.strip():
            task.title = title.strip()

        if status is not None and status in Task.Status.values:
            task.status = status

        if priority is not None and priority in Task.Priority.values:
            task.priority = priority

        if due_date_str is not None:
            try:
                task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except ValueError:
                return False, ResponseMessages.VALIDATION_ERROR, "Invalid due_date format (expected YYYY-MM-DD)", None

        if assigned_to_id is not None:
            if assigned_to_id == "" or assigned_to_id is None:
                task.assigned_to = None
            else:
                try:
                    task.assigned_to = User.objects.get(id=assigned_to_id)
                except User.DoesNotExist:
                    return False, ResponseMessages.NOT_FOUND, "Assigned user not found", None

        task.save()
        task = Task.objects.select_related('project', 'assigned_to').get(id=task.id)
        return True, ResponseMessages.TASK_UPDATED, "Task updated successfully", TaskService._format_task(task)

    @staticmethod
    def delete_task(task_id: int, user):
        try:
            task = Task.objects.select_related('project').get(id=task_id)
        except Task.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Task not found"

        if not ProjectService.is_owner(task.project, user):
            return False, ResponseMessages.FORBIDDEN, ResponseMessages.ONLY_OWNER_CAN_EDIT_TASK

        task.delete()
        return True, ResponseMessages.TASK_DELETED, "Task deleted successfully"

    @staticmethod
    def get_overdue_tasks(user):
        """
        ORM Requirement: Overdue-tasks query.
        Returns tasks where due_date < today and status != Done, filtered for user visibility.
        Uses composite index task_status_duedate_idx.
        """
        overdue_queryset = (
            Task.objects.overdue()
            .select_related('project', 'assigned_to')
            .order_by('due_date')
        )

        visible_tasks = [
            TaskService._format_task(t)
            for t in overdue_queryset
            if t.project.owner_id == user.id or t.assigned_to_id == user.id
        ]
        return True, ResponseMessages.SUCCESS, "Overdue tasks retrieved", visible_tasks
