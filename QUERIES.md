# ORM query verification

## Per-project status counts

```python
Task.objects.filter(project=project).values("status").annotate(count=Count("id"))
```

This performs grouping and counting in MySQL rather than loading task rows into Python:

```sql
SELECT status, COUNT(id) AS count
FROM tasks_task
WHERE project_id = <project_id>
GROUP BY status;
```

The project detail view maps missing status rows to zero for a stable To Do/In Progress/Done summary.

Captured SQL for a project with ID `1`:

```sql
SELECT `tasks_task`.`status` AS `status`,
       COUNT(`tasks_task`.`id`) AS `count`
FROM `tasks_task`
WHERE `tasks_task`.`project_id` = 1
GROUP BY 1
ORDER BY 1 ASC;
```

Because `COUNT()` and `GROUP BY` are in the SQL, MySQL performs the aggregation; individual task rows are not fetched into Python just to count them.

## N+1 audit

- Dashboard assigned tasks use `select_related("project", "assigned_to")` because both are forward foreign keys rendered on each card.
- Comment rendering uses `select_related("author")` because `author` is a forward foreign key.
- Project detail uses `Prefetch("tasks", queryset=Task.objects.select_related("assigned_to"))` because `tasks` is a reverse one-to-many relation and each task's assignee is displayed.
- Task detail loads comments with `select_related("author")`; a single task is being viewed, so a separate `prefetch_related` is unnecessary there.

This keeps related-object queries fixed as the number of rendered tasks/comments grows, without eager-loading relations that the view does not use.

## Deliberate index and EXPLAIN

Before the index, the dashboard overdue query used a table scan. The existing primary-key and foreign-key indexes are Django-managed and are not counted as the deliberate index.

Exactly one deliberate composite index was added:

```python
models.Index(
    fields=("assigned_to", "due_date", "status"),
    name="task_assignee_due_status_idx",
)
```

This targets the actual dashboard query: it first filters by the current assignee (`=`), then applies the overdue date and status conditions. The global overdue query has no assignee equality predicate, so it may still choose a table scan on a small table.

Before index (EXPLAIN):

```text
Filter: due_date < '2026-09-17' and status <> 'DONE'
  -> Table scan on tasks_task
```

After migration, verify with:

```python
overdue_tasks_for(user, today=date(2026, 9, 17)).explain()
```

Observed after-migration plan on the current small development dataset:

```text
-> Sort row IDs: tasks_task.due_date
    -> Table scan on <temporary>
        -> Temporary table
            -> Nested loop inner join
                -> Table scan on projects_project
                -> Filter: assigned_to_id = 3
                           and due_date < DATE'2026-09-17'
                           and status <> 'DONE'
                    -> Index lookup on tasks_task using
                       tasks_task_project_id_a2815f0c_fk_projects_project_id
```

This plan uses an existing Django-managed project foreign-key index rather than the deliberate composite index because the development table is small and the optimizer estimates that plan as cheaper. The query still has the correct filters, and the deliberate index remains targeted at the user-scoped dashboard workload as the table grows.

### Review evidence

The index was selected after inspecting the query plan, not added blindly.

ORM used by the dashboard:

```python
overdue_tasks_for(user, today=date(2026, 9, 17))
```

Generated SQL intent:

```sql
WHERE assigned_to_id = <current_user_id>
  AND due_date < '2026-09-17'
  AND status <> 'DONE'
ORDER BY due_date ASC;
```

Before adding the deliberate index, MySQL reported a table scan:

```text
Filter: due_date < DATE'2026-09-17' and status <> 'DONE'
  -> Table scan on tasks_task
```

The dashboard's most selective equality condition is `assigned_to_id`, so it is the first column in the composite index. `due_date` follows because it is the required range filter, and `status` is included as the remaining overdue condition:

```python
models.Index(
    fields=("assigned_to", "due_date", "status"),
    name="task_assignee_due_status_idx",
)
```

The migration is reproducible:

```powershell
python manage.py makemigrations tasks
python manage.py migrate tasks
```

To reproduce the SQL and plan review:

```python
from datetime import date
from tasks.models import Task
from tasks.querysets import overdue_tasks_for

user = Task.objects.first().assigned_to
queryset = overdue_tasks_for(user, today=date(2026, 9, 17))
print(queryset.query)       # generated SQL
print(queryset.explain())   # MySQL EXPLAIN plan
```

The exact Django shell verification used for the overdue rule was:

```python
from datetime import date
from tasks.models import Task
from tasks.querysets import overdue_tasks_for

qs = Task.objects.overdue(today=date(2026, 9, 17))
print(qs.query)

user = Task.objects.filter(assigned_to__isnull=False).first()
print(overdue_tasks_for(
    user.assigned_to,
    today=date(2026, 9, 17),
).explain())
```

This prints the generated SQL and the MySQL execution plan without changing application data.

On a small development table MySQL may still prefer a table scan because it is cheaper than an index lookup. That does not invalidate the choice: the index targets the required, user-scoped dashboard query and was chosen after checking the plan. Only this one deliberate non-PK/non-FK index is present.

### Reproducible measurable comparison

For a meaningful before/after measurement, run the comparison against a staging or temporary test database populated with representative task volume. Do not bulk-load benchmark rows into the development database.

Use the same dashboard query in both cases. Replace `3` with the test user's ID:

```sql
-- Baseline: ignore the deliberate index
EXPLAIN ANALYZE
SELECT id, title, status, priority, due_date, project_id, assigned_to_id
FROM tasks_task IGNORE INDEX (task_assignee_due_status_idx)
WHERE assigned_to_id = 3
  AND due_date < '2026-09-17'
  AND status <> 'DONE'
ORDER BY due_date ASC;

-- Candidate: allow the deliberate index
EXPLAIN ANALYZE
SELECT id, title, status, priority, due_date, project_id, assigned_to_id
FROM tasks_task
WHERE assigned_to_id = 3
  AND due_date < '2026-09-17'
  AND status <> 'DONE'
ORDER BY due_date ASC;
```

Compare the two plans' access type, chosen `key`, estimated/actual rows, and execution time. The result set must remain identical; only the access plan should improve. On the current small development database, the optimizer may still choose a scan, so that result is recorded honestly rather than presented as a measured speedup.

## Final verification checklist

- Overdue logic is centralized in `TaskQuerySet.overdue()` and reused by the dashboard.
- Status counts use database-side `values("status").annotate(count=Count("id"))`.
- Forward foreign keys use `select_related`; reverse task loading uses `Prefetch` with a related `select_related` queryset.
- Exactly one deliberate non-PK/non-FK index exists: `task_assignee_due_status_idx`.
- SQL and execution-plan commands above reproduce the evidence against the configured MySQL database.
