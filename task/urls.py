from django.urls import path
from task import views

urlpatterns = [
    # Auth API
    path('api/auth/register/', views.api_register, name='api_register'),
    path('api/auth/login/', views.api_login, name='api_login'),
    path('api/auth/logout/', views.api_logout, name='api_logout'),
    path('api/auth/me/', views.api_me, name='api_me'),
    path('api/users/', views.api_users, name='api_users'),

    # Projects API
    path('api/projects/', views.api_projects, name='api_projects'),
    path('api/projects/<int:project_id>/', views.api_project_detail, name='api_project_detail'),
    path('api/projects/<int:project_id>/status-counts/', views.api_project_status_counts, name='api_project_status_counts'),

    # Tasks API
    path('api/tasks/', views.api_tasks, name='api_tasks'),
    path('api/tasks/overdue/', views.api_overdue_tasks, name='api_overdue_tasks'),
    path('api/tasks/<int:task_id>/', views.api_task_detail, name='api_task_detail'),

    # Comments API
    path('api/tasks/<int:task_id>/comments/', views.api_task_comments, name='api_task_comments'),
]