# Backend Folder and File Structure

```text
backend/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── migrations/
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── logging.py
│   ├── auth/
│   │   ├── clerk.py
│   │   └── dependencies.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── account.py
│   │       ├── dashboard.py
│   │       ├── learning_paths.py
│   │       ├── stages.py
│   │       ├── tasks.py
│   │       ├── learning_time.py
│   │       └── weekly_goals.py
│   ├── models/
│   │   ├── user.py
│   │   ├── learning_path.py
│   │   ├── stage.py
│   │   ├── task.py
│   │   ├── link.py
│   │   ├── learning_time.py
│   │   ├── weekly_goal.py
│   │   ├── goal_snapshot.py
│   │   └── task_status_history.py
│   ├── schemas/
│   │   ├── account.py
│   │   ├── dashboard.py
│   │   ├── learning_paths.py
│   │   ├── stages.py
│   │   ├── tasks.py
│   │   ├── learning_time.py
│   │   └── weekly_goals.py
│   ├── services/
│   │   ├── account_deletion.py
│   │   ├── dashboard.py
│   │   ├── learning_paths.py
│   │   ├── stages.py
│   │   ├── tasks.py
│   │   ├── learning_time.py
│   │   └── weekly_goals.py
│   └── worker/
│       └── worker.py
└── tests/
    ├── conftest.py
    ├── unit/
    ├── api/
    └── worker/
```

`app/main.py` reads `API_PREFIX` from application settings and mounts the API router under that prefix, for example `/api/v1`.

The backend uses async SQLAlchemy, with `aiosqlite` for the initial SQLite setup and `asyncpg` for PostgreSQL. API routes handle HTTP concerns and delegate to services. Services enforce business rules and own atomic transactions. Pydantic schemas define request and response contracts separately from ORM models.

The worker entrypoint runs the scheduled weekly-goal snapshot process and reuses the weekly-goal service. Tests are organized by layer and use an isolated temporary SQLite database initially.
