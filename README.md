# TaskFlow

## Project membership

A project member is defined as either the project owner or any user currently assigned to at least one task in that project. Membership is derived from existing relationships; no separate `ProjectMember` table is used.

Members can view the project and all of its tasks. Project and task write operations remain restricted to the project owner.

Comments are append-only. They belong to one task and one author, use oldest-first ordering, cascade when their task is deleted, and are not edited or deleted through the application.

## Django admin

Create an admin account from the project root:

```powershell
python manage.py createsuperuser
```

Start the server and visit [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/). Log in with the superuser credentials to inspect and manage Users, Projects, Tasks, and Comments. Normal users should continue to use the application authentication flow and cannot access the admin interface.
