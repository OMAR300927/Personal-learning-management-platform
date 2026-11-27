# Solution Architecture Plan

## 1. Purpose

This document records the approved technical direction, the rationale behind it, and the architectural boundaries for the Personal Learning Management Platform MVP. Detailed project folders and file structure will be documented separately.

The product requirements and acceptance criteria remain in [spec.md](./spec.md).

## 2. Architectural Style

Use a **modular monolith**:

- One React single-page application (SPA).
- One FastAPI application exposing the backend API.
- One relational application database and a separate managed PostgreSQL instance for the independent deletion ledger.
- A lightweight scheduled worker, using the backend's domain logic, for weekly goal snapshots.

The frontend, API, and worker may be deployed as separate processes, but they remain parts of one product and one codebase. Organize implementation around product domains and keep explicit boundaries between the UI, API, domain rules, persistence, authentication, and background processing.

### Rationale

- The MVP is expected to support thousands of users and does not require the operational overhead of microservices.
- A modular monolith keeps transactions and business rules straightforward while allowing domains to evolve independently.
- The worker needs to run independently of web requests, but does not justify a separate service architecture or message broker initially.

## 3. Technology Decisions

| Area | Decision | Rationale |
|---|---|---|
| Frontend framework | React | Required by the product specification and suitable for the interactive dashboard and management pages. |
| Frontend language and build | TypeScript with Vite | Adds compile-time checks and supports maintainable frontend development with a direct SPA build workflow. |
| Frontend styling | Tailwind CSS | Required by the product specification and supports responsive UI development. |
| Frontend routing | React Router | Provides client-side routing for the application pages and protected navigation. |
| Frontend API state | TanStack Query | Provides a consistent approach to request lifecycle, caching, loading/error states, and mutations. |
| Charts and icons | Recharts and Lucide React | Required by the product specification for data visualization and icons. |
| Backend framework | FastAPI with Pydantic | FastAPI is required and provides typed API validation and generated OpenAPI documentation. |
| Data access and migrations | SQLAlchemy 2 and Alembic | SQLAlchemy handles relational persistence; Alembic tracks and applies schema changes. |
| Database | SQLite initially; PostgreSQL for production | Follows the specified development and production database choices. |
| API protocol | Versioned REST/JSON over HTTPS | A simple fit for the SPA and resource-oriented operations; OpenAPI documents the contract. |
| Identity provider | Clerk | Required for authentication, Google sign-in, and session management. |
| Deletion ledger | Separate managed PostgreSQL instance in production; separate SQLite file locally | Keeps deletion tombstones and Clerk retry state independent of application database backups. |
| Test tools | pytest, Vitest, React Testing Library, and Playwright | Matches the confirmed backend, frontend, and focused browser testing approach. |

No separate payment, maps, or email provider is required for the MVP. Authentication-related email flows are handled through Clerk.

## 4. System Components and Responsibilities

### Web application

- Renders the responsive user interface and supports the agreed login/register flow.
- Uses Clerk's React integration to establish and manage user sessions.
- Sends authenticated requests to the backend over HTTPS.
- Presents API results and validation errors; it is not the authority for business rules or access control.

### Backend API

- Verifies Clerk session JWTs on protected requests.
- Derives the acting user identity from the verified token.
- Enforces ownership and business rules for every operation.
- Validates and persists data, performs dashboard aggregations, and exposes a versioned REST/JSON API.
- Uses shared request validators for titles (maximum 100 characters) and absolute HTTP(S) URLs (maximum 2,048 characters), and returns client errors in a consistent JSON envelope.
- Generates and serves the OpenAPI contract.

### Relational database

- Stores application records and enforces relational integrity.
- Uses PostgreSQL in production and SQLite during the initial development phase.
- Enforces important uniqueness and referential constraints in addition to API-level checks.
- Stores account-deletion tombstones in a separate database. In production, the deletion ledger must use a distinct managed PostgreSQL instance, credentials, and backup/retention domain; local development uses a separate SQLite file.
- Each authenticated request checks the independent ledger before resolving or creating an application user. Ledger unavailability fails closed.

### Weekly-goal snapshot worker

- Detects each user's Saturday–Friday week boundary in that user's timezone.
- Creates immutable goal-progress snapshots representing state as of the boundary, even if execution happens later.
- Uses idempotent writes and safe retries to prevent missing or duplicate snapshots.
- Runs separately from API request handling; no general-purpose queue is required initially.

### Clerk

- Manages registration, login, Google sign-in, and session issuance.
- Provides the identity subject used to associate application records with a user.
- Is accessed server-side for account deletion as needed.

## 5. Frontend and Backend Communication

- The browser communicates with FastAPI using REST/JSON over HTTPS.
- Protected requests include the Clerk session token.
- The backend verifies the token on each protected request and derives the user identity from its trusted claims.
- The client must not supply or override the authoritative owner ID.
- API routes should be versioned (for example, `/api/v1`) and documented through FastAPI's OpenAPI output.
- The backend remains authoritative for validation, authorization, calculations, and persistence. Frontend validation is for user experience and does not replace server-side validation.

## 6. Data and Persistence Boundaries

The high-level relational model includes:

- Users, keyed by their Clerk subject and containing the user's timezone.
- Learning paths, stages, tasks, and links.
- Path-level learning-time entries.
- Weekly goals and immutable goal snapshots.
- Timestamped task-status history needed to reconstruct task state at week boundaries.
- Relevant change history retained until a corresponding snapshot is finalized.

All user-owned records must be scoped to their owner. Use foreign keys and database constraints to protect relationships and prevent invalid cross-account references. Enforce the one-goal-per-week/type/scope rule with a database uniqueness constraint as well as application validation.

### Time and weekly snapshots

- Store the date/time when learning occurred so week assignment can be calculated using the user's timezone.
- A timezone change recalculates learning-entry week groupings.
- Learning-time entries assigned to ended weeks are locked against edits and deletion.
- Task statuses remain editable. Timestamped status changes are retained so the worker can determine the task status at the exact end of a week.
- Preserve the required change history, including relevant task lifecycle changes, until the corresponding snapshot has been finalized.
- Once written, a goal snapshot is immutable. A delayed or retried worker must not rewrite a finalized snapshot.
- Calendar-month reporting uses the product's defined calendar-month boundaries.

#### Week-boundary edge-case decisions

- Snapshot reconstruction uses the state that existed at the exact user-local week boundary. If a path or task is deleted before delayed snapshot processing but existed at that boundary, its boundary state still contributes to the snapshot.
- If a path-specific goal is deleted with its path before snapshot processing, the worker still creates the historical snapshot for that goal when it existed at the boundary. The snapshot is retained independently of the deleted live records.
- A timezone change regroups only learning-time entries whose weeks have not been finalized. Entries are recalculated using the new timezone and may become locked if their recalculated week has ended.
- Finalized learning-time history and goal snapshots are immutable. A timezone change never rewrites an existing finalized snapshot or its historical results.

## 7. Authentication, Authorization, and Account Deletion

### Authentication and authorization

- Use Clerk's React integration for user authentication and session UX.
- FastAPI verifies Clerk JWT signature and issuer using Clerk's published verification keys, and checks the `azp` claim against configured authorized frontend origins. Standard Clerk session tokens do not require a configured audience.
- Every protected operation derives the user ID from the verified token and scopes database access to that user.
- Never rely on frontend route protection as the sole authorization control.
- Return appropriate unauthenticated/forbidden responses; the frontend handles the specified expired-session message, login redirect, return destination, and preservation of unsaved changes.

### Account deletion

Account deletion spans the application database and Clerk, so it cannot be one atomic transaction. Use an idempotent deletion workflow that:

1. Revokes or blocks access to the account immediately.
2. Writes a durable deletion record to the independent deletion ledger; this tombstone is the access-blocking source of truth.
3. Deletes the user's live application records and related history.
4. Requests Clerk identity deletion, retrying safely if that external operation temporarily fails.
5. Records operational success/failure without logging tokens or learning content, and alerts operators when retries require attention.

Encrypted database backups may retain deleted-user data until the documented retention period expires. Backup retention and expiry must be enforced automatically. The deletion ledger must be stored independently of application database backups and remain available if an application backup is restored. Keep each deletion record until every backup capable of restoring that account has expired. Before restored application data is made accessible, the restore procedure must replay the ledger and remove or block every account recorded as deleted.

The API replays all ledger tombstones during startup and does not serve requests if replay fails. Apply the independent ledger schema with `uv run alembic -c alembic-deletion-ledger.ini upgrade head` before starting the API. The scheduled backend worker retries pending Clerk deletions; deployment monitoring must alert on the `account_deletion_clerk_retry_required`, `account_deletion_database_failure`, `account_deletion_ledger_access_check_failed`, and `account_deletion_restore_replay_failure` log events.

### Data protection and backup deletion

- Production database storage and backups must be encrypted at rest. All production client-to-service communication must use HTTPS/TLS.
- Clerk manages authentication credentials, including password storage and password hashing. The application does not store user passwords.
- Application-level per-user encryption, envelope encryption, KMS integration for per-user keys, and immediate cryptographic erasure are out of MVP scope.
- Google Cloud KMS will not be integrated for per-user application data encryption in the MVP.
- Backup retention duration and production providers remain operational decisions. They must be resolved before production launch with automatic backup expiry and independent ledger durability in place.

## 8. Background Processing

Use one lightweight scheduled worker for weekly goal snapshot finalization and retrying pending Clerk account deletions. It should share backend domain rules rather than reimplementing them.

- Use each user's timezone to determine the boundary.
- Reconstruct state as of the boundary using timestamped changes.
- Store snapshots atomically and enforce uniqueness so reruns are safe.
- Retry transient failures and surface persistent failures through monitoring/alerts.
- Schedule the worker frequently enough for account-deletion retries; set and monitor its production cadence as part of T-031.
- Do not add a queue or separate job platform unless later operational needs require one.

## 9. External Integrations

- **Clerk:** Authentication, sessions, Google sign-in, and identity deletion.
- **Managed hosting and backup storage:** Provider selection remains open. Selection must support deployment, application and independent ledger databases, worker scheduling, secrets, encryption at rest, backup retention/expiry, and restoration from the deletion ledger.
- No other external integrations are required for the MVP.

## 10. Security and Operational Considerations

- Require HTTPS in production and store secrets in the hosting provider's secret-management facility.
- Restrict browser CORS access to the deployed frontend origin.
- Validate all inputs on the backend, including title and URL limits and URL validity.
- Safely render user-provided text and links; do not treat them as trusted HTML.
- Consider rate limits for authentication-adjacent and write endpoints.
- Do not log session tokens, passwords, encryption keys, or users' learning content.
- Monitor API errors, database availability, worker execution, snapshot failures, and account-deletion retries.
- Encrypt production database storage and backups at rest, use HTTPS/TLS, and keep application passwords delegated to Clerk.
- Automatically expire encrypted backups according to the documented retention policy.
- Keep the deletion ledger independent of application-backup restoration and replay it before restored data becomes accessible.

## 11. Testing Strategy

- Backend unit and API tests use pytest and an isolated temporary SQLite database initially.
- Frontend unit and component tests use Vitest and React Testing Library.
- A focused Playwright suite covers critical user journeys.
- Routine automated tests mock or stub external services. A controlled smoke test verifies the real Clerk integration.
- Tests prioritize critical behavior and acceptance criteria; no initial coverage percentage is required.
- Tests are run locally for now. Pull-request CI automation is not yet decided.
- When the production database migration to PostgreSQL is undertaken, add and run PostgreSQL-backed integration tests as part of that migration.

## 12. Hosting and Deployment

- Managed hosting is approved; the specific vendors and production domain remain undecided.
- Prefer a deployment that can run the web app, FastAPI API, PostgreSQL, and scheduled worker with secure secret management, encrypted backups, retention expiry, and independent deletion-ledger support.
- Keep the frontend and API behind one application domain where practical, while preserving clear service boundaries.
- Deploy database schema changes through Alembic migrations.
- Select providers only after confirming regions, operational fit, cost, encryption at rest, backup retention/expiry, and restore behavior.

## 13. Architectural Boundaries

- **Frontend vs. backend:** UI state and presentation belong in the frontend; security-sensitive decisions, validation, business rules, and data access belong in the backend.
- **Identity vs. application profile:** Clerk is the identity authority; the application stores only the identity reference and product-specific user settings/data.
- **Domain vs. transport:** API handlers translate HTTP requests and responses; domain logic should not depend on React, HTTP details, or Clerk SDK behavior.
- **Domain vs. persistence:** Product rules should be testable independently where practical; database constraints provide integrity enforcement but do not replace domain validation.
- **Worker vs. request handling:** Week-close snapshots run asynchronously and must not depend on a user opening the app.
- **Snapshot vs. live state:** Current task and time data may change according to product rules; finalized weekly goal snapshots are historical records and do not change.
- **MVP vs. future scope:** No microservices, message broker, AI services, collaboration, or additional external integrations are introduced without a separate product/architecture decision.

## 14. Decisions Still Open

- Managed hosting/database/backup vendors and regions.
- Backup retention duration and the managed providers for the application database, deletion ledger, and backups.
- Production domain and deployment regions.
- When pull-request test automation should be introduced.
- PostgreSQL test execution is deferred until the production database migration work.
