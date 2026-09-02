from django.utils import timezone
from task.models import Task
from task.services.task_service import TaskService
from task.utils.response.messages import ResponseMessages


class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user):
        """
        Returns current user's assigned tasks, grouped into three columns: TODO, IN_PROGRESS, DONE.
        """
        user_tasks = (
            Task.objects.filter(assigned_to=user)
            .select_related('project', 'assigned_to')
            .order_by('due_date', '-priority')
        )

        today = timezone.now().date()

        columns = {
            "TODO": [],
            "IN_PROGRESS": [],
            "DONE": []
        }

        overdue_count = 0

        for t in user_tasks:
            formatted = TaskService._format_task(t)
            if t.status in columns:
                columns[t.status].append(formatted)
            else:
                columns["TODO"].append(formatted)

            if t.due_date < today and t.status != Task.Status.DONE:
                overdue_count += 1

        dashboard_payload = {
            "columns": {
                "TODO": {
                    "label": "To Do",
                    "count": len(columns["TODO"]),
                    "tasks": columns["TODO"]
                },
                "IN_PROGRESS": {
                    "label": "In Progress",
                    "count": len(columns["IN_PROGRESS"]),
                    "tasks": columns["IN_PROGRESS"]
                },
                "DONE": {
                    "label": "Done",
                    "count": len(columns["DONE"]),
                    "tasks": columns["DONE"]
                }
            },
            "summary": {
                "total_assigned": len(user_tasks),
                "overdue_count": overdue_count
            }
        }

        return True, ResponseMessages.SUCCESS, "Dashboard data loaded", dashboard_payload
