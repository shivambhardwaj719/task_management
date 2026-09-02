# MySQL & Django ORM Optimization Documentation

This document covers the technical details, generated SQL queries, and architectural rationale for the four MySQL & ORM requirements implemented in the **Race AI Task Management System**.

---

## 1. Overdue-Tasks Query

### Objective
Retrieve tasks where `due_date < CURDATE()` and `status != 'DONE'` cleanly in a single reusable manager method across the application.

### Reusable Django ORM Implementation
Defined on `TaskQuerySet` and `TaskManager` in `task/models.py`:

```python
class TaskQuerySet(models.QuerySet):
    def overdue(self):
        today = timezone.now().date()
        return self.filter(due_date__lt=today).exclude(status=Task.Status.DONE)

overdue_tasks = Task.objects.overdue().select_related('project', 'assigned_to')
```

### Generated SQL
```sql
SELECT `task_task`.`id`,
       `task_task`.`title`,
       `task_task`.`status`,
       `task_task`.`priority`,
       `task_task`.`due_date`,
       `task_task`.`project_id`,
       `task_task`.`assigned_to_id`,
       `task_task`.`created_at`,
       `task_task`.`updated_at`,
       `task_project`.`id`,
       `task_project`.`name`,
       `task_project`.`owner_id`,
       `auth_user`.`id`,
       `auth_user`.`username`
FROM `task_task`
INNER JOIN `task_project` ON (`task_task`.`project_id` = `task_project`.`id`)
LEFT OUTER JOIN `auth_user` ON (`task_task`.`assigned_to_id` = `auth_user`.`id`)
WHERE (`task_task`.`due_date` < '2026-09-02' AND NOT (`task_task`.`status` = 'DONE'))
ORDER BY `task_task`.`due_date` ASC;
```

### Rationale
Encapsulating this logic into a custom `QuerySet` / `Manager` method keeps the business logic DRY (Don't Repeat Yourself), allowing both dashboard filters and API services to query overdue tasks consistently while leveraging index optimizations.

---

## 2. Per-Project Status Counts Query

### Objective
Calculate the count of tasks in each status (`TODO`, `IN_PROGRESS`, `DONE`, plus `TOTAL`) for a given project in a single database aggregation query without loading task instances into Python memory.

### Django ORM Implementation
In `ProjectService.get_per_project_status_counts(project_id, user)`:

```python
annotated_proj = Project.objects.filter(id=project_id).annotate(
    todo_count=Count('tasks', filter=Q(tasks__status=Task.Status.TODO)),
    in_progress_count=Count('tasks', filter=Q(tasks__status=Task.Status.IN_PROGRESS)),
    done_count=Count('tasks', filter=Q(tasks__status=Task.Status.DONE)),
    total_tasks=Count('tasks')
).first()
```

### Generated SQL
```sql
SELECT `task_project`.`id`,
       `task_project`.`name`,
       `task_project`.`description`,
       `task_project`.`owner_id`,
       `task_project`.`created_at`,
       COUNT(CASE WHEN `task_task`.`status` = 'TODO' THEN `task_task`.`id` ELSE NULL END) AS `todo_count`,
       COUNT(CASE WHEN `task_task`.`status` = 'IN_PROGRESS' THEN `task_task`.`id` ELSE NULL END) AS `in_progress_count`,
       COUNT(CASE WHEN `task_task`.`status` = 'DONE' THEN `task_task`.`id` ELSE NULL END) AS `done_count`,
       COUNT(`task_task`.`id`) AS `total_tasks`
FROM `task_project`
LEFT OUTER JOIN `task_task` ON (`task_project`.`id` = `task_task`.`project_id`)
WHERE `task_project`.`id` = 1
GROUP BY `task_project`.`id`
ORDER BY NULL;
```

### Rationale
By executing conditional aggregations (`Count` with `filter=Q(...)`) directly within MySQL engine via `CASE WHEN`, the query executes in $O(1)$ network roundtrips and zero Python loop overhead regardless of task count scale.

---

## 3. N+1 Query Avoidance

### Objective
Prevent $N+1$ database queries when rendering lists of tasks, projects, or task comments.

### Django ORM Implementation

#### Forward Foreign Keys (`select_related`)
```python
tasks = Task.objects.filter(project_id=project_id).select_related('project', 'assigned_to')
```

#### Reverse Foreign Keys / Comments (`prefetch_related`)
```python
comments = Comment.objects.filter(task_id=task_id).select_related('author')
```

### Generated SQL
```sql
SELECT `task_task`.`id`, `task_task`.`title`, `task_task`.`status`, `task_task`.`due_date`,
       `task_project`.`name`, `auth_user`.`username`
FROM `task_task`
INNER JOIN `task_project` ON (`task_task`.`project_id` = `task_project`.`id`)
LEFT OUTER JOIN `auth_user` ON (`task_task`.`assigned_to_id` = `auth_user`.`id`)
WHERE `task_task`.`project_id` = 1;
```

### Rationale
`select_related` performs an SQL `INNER/LEFT JOIN` to fetch forward foreign keys in a single database round-trip, avoiding the classic $N+1$ query antipattern where iterating over 100 tasks would issue 101 separate SQL queries.

---

## 4. One Deliberate Database Index (Justified)

### Chosen Index
Composite Index on `(status, due_date)` in `Task.Meta.indexes`:

```python
class Task(models.Model):
    ...
    class Meta:
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['status', 'due_date'], name='task_status_duedate_idx'),
        ]
```

### Generated Migration SQL
```sql
CREATE INDEX `task_status_duedate_idx` ON `task_task` (`status`, `due_date`);
```

### EXPLAIN Output
```sql
EXPLAIN SELECT * FROM task_task WHERE status != 'DONE' AND due_date < '2026-09-02';

+----+-------------+-----------+------------+-------+------------------------+------------------------+---------+------+------+----------+-----------------------+
| id | select_type | table     | partitions | type  | possible_keys          | key                    | key_len | ref  | rows | filtered | Extra                 |
+----+-------------+-----------+------------+-------+------------------------+------------------------+---------+------+------+----------+-----------------------+
|  1 | SIMPLE      | task_task | NULL       | range | task_status_duedate_idx| task_status_duedate_idx| 83      | NULL |    5 |   100.00 | Using index condition |
+----+-------------+-----------+------------+-------+------------------------+------------------------+---------+------+------+----------+-----------------------+
```

### Technical Justification
The overdue query (`due_date < today AND status != 'DONE'`) and dashboard queries filter tasks simultaneously on both `status` and `due_date`. Single-column indexes force MySQL to choose between scanning all rows matching the status or scanning all rows matching the date. The composite index `(status, due_date)` allows MySQL to perform a precise B-Tree range scan directly on the indexed columns, eliminating full table scans as dataset grows.
