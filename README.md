# TaskFlow

A multi-user task manager built with Django and MySQL for the Race Ai assignment. Users manage projects, assign tasks, discuss work through comments, and track their assigned tasks by status and overdue date.

**Database design and query evidence:** [QUERIES.md](QUERIES.md)

## Features and access

- Django registration, login, and POST-based logout.
- Project and task CRUD with server-side ownership checks.
- Tasks assignable to any user, with fixed status/priority choices and required deadlines.
- Append-only task comments with server-assigned authors.
- My Tasks dashboard grouped into To Do, In Progress, and Done, with an overdue section.

| Action within a project | Owner | Assigned member | Unrelated user |
| --- | --- | --- | --- |
| View project and all tasks; add comments | Yes | Yes | No |
| Edit/delete project; create/edit/delete tasks | Yes | No | No |

Any authenticated user can create a project and becomes its owner. A member is the owner or a user currently assigned to at least one task in the project. Reassigning their last task removes derived membership. Django admin is a separate staff interface.

## Local setup

Verified local versions: **Python 3.13.7, Django 6.1.1, MySQL Community Server 8.4.11, mysqlclient 2.3.0**. Commands below use Windows PowerShell and assume Python and MySQL Server are installed, with MySQL running on `127.0.0.1:3306`.

### 1. Clone and install

```powershell
git clone https://github.com/Bhavish-Makkar/Task-Manager.git
cd Task-Manager
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Dependencies in `requirements.txt` are currently unpinned; the versions above describe the verified local environment. If activation is unavailable, use `.\env\Scripts\python.exe` instead of `python` in subsequent commands.

### 2. Prepare MySQL

Install/start MySQL Community Server 8.4 locally, then open its client as an administrator:

```powershell
mysql -u root -p
```

Run the following SQL, replacing the example password:

```sql
CREATE DATABASE race_ai CHARACTER SET utf8mb4;
CREATE USER 'race_ai_app'@'localhost' IDENTIFIED BY 'replace-with-your-local-password';
GRANT ALL PRIVILEGES ON race_ai.* TO 'race_ai_app'@'localhost';
GRANT ALL PRIVILEGES ON test_race_ai.* TO 'race_ai_app'@'localhost';
```

The second database grant lets Django create and remove its isolated test database. These are local development credentials.

### 3. Configure the environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` to match your MySQL account:

```dotenv
MYSQL_DATABASE=race_ai
MYSQL_USER=race_ai_app
MYSQL_PASSWORD=replace-with-your-local-password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

Django loads this file automatically. Keep `.env` out of Git; `.env.example` documents the required variables. Current settings use UTC and development mode (`DEBUG=True`).

### 4. Migrate and run

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [Login](http://127.0.0.1:8000/login/), [Register](http://127.0.0.1:8000/register/), or [Django admin](http://127.0.0.1:8000/admin/). After login, the landing page is [My Tasks](http://127.0.0.1:8000/dashboard/). Use the Projects navigation to create a project and add tasks.

## Tests and quick demo

```powershell
python manage.py test
# Reuse the isolated test database and show individual test names:
python manage.py test --keepdb -v 2
```

Tests live in each app's `tests.py`. Django uses `test_race_ai`, separate from the development database. Only one test run should use that database at a time.

For a quick manual demo, register two users. As the first user, create a project and assign a task to the second. The second user can view all tasks in that project and comment, but cannot modify them. Their dashboard shows only their own assignments. Set an unfinished task's deadline before today to see it in Overdue.

## Design assumptions

- Task creation is restricted to the project owner, matching task management permissions.
- Project description is optional; task deadline is required. Past deadlines are allowed.
- Overdue means `due_date < current local date` and status is not Done. Due today is not overdue; The current date is derived using Django's configured timezone (UTC in this project).
- Deleting a project cascades to its tasks and comments. Deleting an assignee sets assignment to null; deleting a comment author deletes their comments.
- Comments have no user-facing edit/delete flow. Admin comment fields are read-only; administrative deletion remains available.
- Exactly one deliberate composite index is defined beyond automatic PK/FK indexes. Its rationale and observed optimizer plan are in [QUERIES.md](QUERIES.md); the small dataset does not establish a measured speedup.

## Code map

`accounts/` handles authentication and dashboard views; `projects/` contains ownership and membership checks; `tasks/` contains task CRUD and reusable queries; `comments/` contains comment creation. Shared UI assets live in `templates/` and `static/`.
