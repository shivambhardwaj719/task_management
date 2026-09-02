from django.db.models import Count, Q
from task.models import Project, Task
from task.utils.response.messages import ResponseMessages

class ProjectService:
    @staticmethod
    def is_owner(project: Project, user) -> bool:
        return project.owner_id == user.id

    @staticmethod
    def is_member(project: Project, user) -> bool:
        """Project member: owner or anyone assigned to a task in the project."""
        if project.owner_id == user.id:
            return True
        return Task.objects.filter(project=project, assigned_to=user).exists()

    @staticmethod
    def list_projects_for_user(user):
        """Lists projects owned by user or where user is assigned to a task (N+1 optimized with select_related)."""
        projects = (
            Project.objects.filter(
                Q(owner=user) | Q(tasks__assigned_to=user)
            )
            .distinct()
            .select_related('owner')
            .prefetch_related('tasks')
        )
        data = []
        for p in projects:
            data.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "owner_id": p.owner_id,
                "owner_username": p.owner.username,
                "is_owner": p.owner_id == user.id,
                "created_at": p.created_at.isoformat()
            })
        return data

    @staticmethod
    def get_project_by_id(project_id: int, user):
        try:
            project = Project.objects.select_related('owner').get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found", None

        if not ProjectService.is_member(project, user):
            return False, ResponseMessages.FORBIDDEN, "You do not have access to view this project", None

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "owner_username": project.owner.username,
            "is_owner": project.owner_id == user.id,
            "created_at": project.created_at.isoformat()
        }
        return True, ResponseMessages.SUCCESS, "Project fetched successfully", project_data

    @staticmethod
    def create_project(name: str, description: str, owner_user):
        if not name or not name.strip():
            return False, ResponseMessages.VALIDATION_ERROR, "Project name is required", None

        project = Project.objects.create(
            name=name.strip(),
            description=description.strip() if description else '',
            owner=owner_user
        )
        data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "owner_username": owner_user.username,
            "created_at": project.created_at.isoformat()
        }
        return True, ResponseMessages.PROJECT_CREATED, "Project created successfully", data

    @staticmethod
    def update_project(project_id: int, name: str, description: str, user):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found", None

        if not ProjectService.is_owner(project, user):
            return False, ResponseMessages.FORBIDDEN, ResponseMessages.ONLY_OWNER_CAN_EDIT_PROJECT, None

        if name and name.strip():
            project.name = name.strip()
        if description is not None:
            project.description = description.strip()

        project.save()
        data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "owner_username": project.owner.username
        }
        return True, ResponseMessages.PROJECT_UPDATED, "Project updated successfully", data

    @staticmethod
    def delete_project(project_id: int, user):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found"

        if not ProjectService.is_owner(project, user):
            return False, ResponseMessages.FORBIDDEN, ResponseMessages.ONLY_OWNER_CAN_EDIT_PROJECT

        project.delete()
        return True, ResponseMessages.PROJECT_DELETED, "Project deleted successfully"

    @staticmethod
    def get_per_project_status_counts(project_id: int, user):
        """
        OR M Requirement: Per-project status counts.
        Uses single query with annotate and Count with Q filter rather than fetching tasks in Python.
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False, ResponseMessages.NOT_FOUND, "Project not found", None

        if not ProjectService.is_member(project, user):
            return False, ResponseMessages.FORBIDDEN, "Access denied", None

        annotated_proj = Project.objects.filter(id=project_id).annotate(
            todo_count=Count('tasks', filter=Q(tasks__status=Task.Status.TODO)),
            in_progress_count=Count('tasks', filter=Q(tasks__status=Task.Status.IN_PROGRESS)),
            done_count=Count('tasks', filter=Q(tasks__status=Task.Status.DONE)),
            total_tasks=Count('tasks')
        ).first()

        data = {
            "project_id": project_id,
            "project_name": project.name,
            "counts": {
                "TODO": annotated_proj.todo_count,
                "IN_PROGRESS": annotated_proj.in_progress_count,
                "DONE": annotated_proj.done_count,
                "TOTAL": annotated_proj.total_tasks
            }
        }
        return True, ResponseMessages.SUCCESS, "Status counts calculated", data
