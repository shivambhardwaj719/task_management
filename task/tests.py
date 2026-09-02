from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from task.models import Project, Task, Comment
from task.services.project_service import ProjectService
from task.services.task_service import TaskService
from task.utils.response.messages import ResponseMessages


class TaskManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='password123')
        self.member = User.objects.create_user(username='member', password='password123')
        self.stranger = User.objects.create_user(username='stranger', password='password123')

        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.owner
        )

        self.task_todo = Task.objects.create(
            title='Task TODO',
            status=Task.Status.TODO,
            priority=Task.Priority.HIGH,
            due_date=date.today() - timedelta(days=2),
            project=self.project,
            assigned_to=self.member
        )

        self.task_inprogress = Task.objects.create(
            title='Task In Progress',
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.MEDIUM,
            due_date=date.today() + timedelta(days=5),
            project=self.project,
            assigned_to=self.member
        )

        self.task_done = Task.objects.create(
            title='Task Done',
            status=Task.Status.DONE,
            priority=Task.Priority.LOW,
            due_date=date.today() - timedelta(days=1),
            project=self.project,
            assigned_to=self.owner
        )

        self.client = Client()

    def test_overdue_tasks_queryset(self):
        """Test that Task.objects.overdue() returns only tasks with due_date < today and status != DONE."""
        overdue_tasks = list(Task.objects.overdue())
        self.assertEqual(len(overdue_tasks), 1)
        self.assertEqual(overdue_tasks[0].id, self.task_todo.id)

    def test_per_project_status_counts(self):
        """Test per-project status counts calculated in a single query."""
        success, code, msg, data = ProjectService.get_per_project_status_counts(self.project.id, self.owner)
        self.assertTrue(success)
        counts = data['counts']
        self.assertEqual(counts['TODO'], 1)
        self.assertEqual(counts['IN_PROGRESS'], 1)
        self.assertEqual(counts['DONE'], 1)
        self.assertEqual(counts['TOTAL'], 3)

    def test_ownership_permission_enforcement(self):
        """Test that non-owners cannot edit or delete projects or tasks."""
        success, code, msg, data = ProjectService.update_project(
            self.project.id, name='Hacked Name', description='', user=self.stranger
        )
        self.assertFalse(success)
        self.assertEqual(code, ResponseMessages.FORBIDDEN)

        success, code, msg = ProjectService.delete_project(self.project.id, user=self.stranger)
        self.assertFalse(success)
        self.assertEqual(code, ResponseMessages.FORBIDDEN)

        success, code, msg, data = TaskService.update_task(
            self.task_todo.id, title='Hacked Task', user=self.stranger
        )
        self.assertFalse(success)
        self.assertEqual(code, ResponseMessages.FORBIDDEN)

        success, code, msg, data = ProjectService.update_project(
            self.project.id, name='Updated Project', description='', user=self.owner
        )
        self.assertTrue(success)

    def test_n_plus_one_avoidance(self):
        """Test select_related on task lists avoids N+1 queries."""
        with self.assertNumQueries(1):
            tasks = list(Task.objects.filter(project=self.project).select_related('project', 'assigned_to'))
            for t in tasks:
                _ = t.project.name
                _ = t.assigned_to.username if t.assigned_to else ""

    def test_api_permission_layer(self):
        """Test API endpoints enforce ownership permissions at HTTP level."""
        self.client.login(username='stranger', password='password123')

        response = self.client.put(
            f'/api/projects/{self.project.id}/',
            data={'name': 'Malicious Edit'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(f'/api/tasks/{self.task_todo.id}/')
        self.assertEqual(response.status_code, 403)
