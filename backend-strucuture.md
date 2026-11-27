# Backend Folder and File Structure

```text
backend/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── migrations/
│   ├── env.py
│   └── versions/
├── deletion_ledger_migrations/
│   ├── env.py
│   └── versions/
├── alembic-deletion-ledger.ini
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   └── validation.py
│   ├── auth/
│   │   ├── clerk.py
│   │   └── dependencies.py
│   ├── db/
│   │   ├── base.py
│   │   ├── deletion_ledger.py
│   │   ├── deletion_ledger_base.py
│   │   └── session.py
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── account.py
│   │       ├── dashboard.py
│   │       ├── learning_paths.py
│   │       ├── learning_time.py
│   │       ├── links.py
│   │       └── weekly_goals.py
│   ├── models/
│   │   ├── deletion_record.py
│   │   ├── user.py
│   │   ├── learning_path.py
│   │   ├── stage.py
│   │   ├── task.py
│   │   ├── link.py
│   │   ├── learning_time.py
│   │   ├── weekly_goal.py
│   │   └── goal_snapshot.py
│   ├── schemas/
│   │   ├── account.py
│   │   ├── dashboard.py
│   │   ├── errors.py
│   │   ├── learning_paths.py
│   │   ├── learning_time.py
│   │   ├── links.py
│   │   └── weekly_goals.py
│   ├── services/
│   │   ├── account_deletion.py
│   │   ├── dashboard.py
│   │   ├── learning_paths.py
│   │   ├── learning_time.py
│   │   ├── links.py
│   │   ├── ownership.py
│   │   ├── tasks.py
│   │   ├── users.py
│   │   └── weekly_goals.py
│   ├── worker/
│   │   └── worker.py
│   └── lib/
│       └── week.py
└── tests/
    ├── conftest.py
    ├── unit/
    ├── api/
    └── worker/
```

`app/main.py` reads `API_PREFIX` from application settings and mounts the API router under that prefix, for example `/api/v1`.

The backend uses async SQLAlchemy, with `aiosqlite` for the initial SQLite setup and `asyncpg` for PostgreSQL. API routes handle HTTP concerns and delegate to services. Services enforce business rules and own atomic transactions. Pydantic schemas define request and response contracts separately from ORM models.

The worker entrypoint finalizes weekly-goal snapshots and retries pending Clerk deletions. The independent ledger has a separate Alembic configuration and database. Tests are organized by layer and use isolated temporary SQLite databases initially.
