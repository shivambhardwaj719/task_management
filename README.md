# Task Management System (Django + MySQL)

A robust, multi-user task management application built with **Django 5 / Python 3.12** backed by **MySQL 8.0**. Designed with clean service-oriented architecture, standardized HTTP response handlers, strict ownership permission enforcement, ORM N+1 query avoidance, custom query managers, per-project status aggregation, a deliberate composite database index, and a modern glassmorphic dashboard UI.

---

## Key Features

- **Authentication**: Built-in User authentication (register, login, logout, me endpoints).
- **Projects**: Full CRUD for authenticated users. Only the project owner can edit or delete a project.
- **Tasks**: Full CRUD with status (`To Do`, `In Progress`, `Done`) and priority (`Low`, `Medium`, `High`) fixed choice sets. Only project owners can edit/delete tasks within their project.
- **Task Assignment**: Tasks can be assigned to any user.
- **Append-Only Comments**: Any project member can comment on tasks.
- **Interactive Dashboard**: A responsive 3-column Kanban interface (To Do / In Progress / Done) displaying user's assigned tasks and live status counts.
- **Overdue Task Tracking**: Quick filter for overdue tasks (`due_date < today` and `status != Done`).
- **Standard Response Messages**: Standardized JSON responses (`success_response`, `bad_request_response`, `forbidden_response`, etc.) and message catalog.
- **Service Layer Pattern**: All core business logic separated from views into reusable service modules (`services/`).

---

## Technical Stack & Architecture

- **Backend Framework**: Django 5 / Python 3.12
- **Database**: MySQL 8.0 (configured with PyMySQL / mysqlclient)
- **Containerization**: Docker & Docker Compose
- **Response Utilities**:
  - `utils/response/messages.py`: Predefined system messages (`ResponseMessages`).
  - `utils/response/handlers.py`: Standardized HTTP JSON response handlers.
- **Service Layer**:
  - `services/auth_service.py`
  - `services/project_service.py`
  - `services/task_service.py`
  - `services/comment_service.py`
  - `services/dashboard_service.py`

---

## Getting Started & Local Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (for running MySQL)

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <repository-url>
cd task_management

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
# Or manually:
pip install Django pymysql cryptography
```

### Step 3: Stand Up MySQL Container (Docker Compose)
Start the MySQL 8.0 database container in the background:
```bash
docker compose up -d
```
*Database credentials configured in `docker-compose.yml` and `.env`:*
- **Database**: `task_db`
- **User**: `task_user`
- **Password**: `task_pass`
- **Port**: `3306`

### Step 4: Environment Variables Setup
Copy `.env.example` to `.env` if not present:
```bash
cp .env.example .env
```

### Step 5: Run Database Migrations
```bash
python manage.py migrate
```

### Step 6: Create Admin / Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## Running Automated Tests

Run the unit test suite to verify permissions, ORM queries, overdue filtering, and N+1 query avoidance:
```bash
python manage.py test task
```

---

## MySQL & ORM Optimization Summary

Detailed write-up, SQL logs, and `EXPLAIN` query execution plans can be found in [QUERIES.md](QUERIES.md).

1. **Overdue-Tasks Query**: Encapsulated in custom `TaskManager.overdue()` queryset method (`due_date < today` and `status != DONE`).
2. **Per-Project Status Counts**: Calculated using `Project.objects.annotate(todo_count=Count('tasks', filter=Q(...)))` in single SQL query instead of Python loops.
3. **N+1 Avoidance**: Forward foreign keys loaded using `select_related('project', 'assigned_to')` and reverse relations pre-fetched using `prefetch_related`.
4. **Deliberate Composite Index**: `models.Index(fields=['status', 'due_date'], name='task_status_duedate_idx')` added to `Task.Meta` to optimize range scans for overdue tasks.

---

## Git Commit History Strategy

Commits in this repository follow step-by-step feature progression:
1. `c25bd99`: `feat: initialize Django project with Docker MySQL config and environment setup`
2. `92648bc`: `feat: add standardized response messages and response handlers layer`
3. `6a12316`: `feat: add Project, Task, and Comment models with custom manager and status_duedate composite index`
4. `bff4e14`: `feat: implement business logic service layer for auth, projects, tasks, comments, and dashboard`
5. `900b4a3`: `feat: add API views and URL routing with strict permission validation and standardized responses`
6. `bb4cf59`: `feat: build responsive glassmorphism Kanban dashboard UI with real-time API integrations`
7. `feat: add comprehensive automated test suite, QUERIES.md, and documentation`
