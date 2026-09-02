from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from task.enums import TaskStatus, TaskPriority, Status, Priority


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TaskQuerySet(models.QuerySet):
    def overdue(self):
        today = timezone.now().date()
        return self.filter(due_date__lt=today).exclude(status=TaskStatus.DONE)

    def assigned_to_user(self, user):
        return self.filter(assigned_to=user)


class TaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)

    def overdue(self):
        return self.get_queryset().overdue()

    def assigned_to_user(self, user):
        return self.get_queryset().assigned_to_user(user)


class Task(models.Model):
    Status = TaskStatus
    Priority = TaskPriority

    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO
    )
    priority = models.CharField(
        max_length=20, choices=TaskPriority.choices, default=TaskPriority.MEDIUM
    )
    due_date = models.DateField()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskManager()

    class Meta:
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(
                fields=['status', 'due_date'], name='task_status_duedate_idx'
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class Comment(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
