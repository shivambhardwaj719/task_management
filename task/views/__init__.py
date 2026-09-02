from task.views.auth_views import (
    api_register,
    api_login,
    api_logout,
    api_me,
    api_users,
)
from task.views.project_views import (
    api_projects,
    api_project_detail,
    api_project_status_counts,
)
from task.views.task_views import (
    api_tasks,
    api_task_detail,
    api_overdue_tasks,
)
from task.views.comment_views import (
    api_task_comments,
)
from task.views.dashboard_views import (
    index_view,
    api_dashboard,
)

__all__ = [
    'api_register',
    'api_login',
    'api_logout',
    'api_me',
    'api_users',
    'api_projects',
    'api_project_detail',
    'api_project_status_counts',
    'api_tasks',
    'api_task_detail',
    'api_overdue_tasks',
    'api_task_comments',
    'index_view',
    'api_dashboard',
]
