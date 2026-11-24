# Implementation Tasks

This plan follows a backend-first workflow: complete and verify the backend API before building the frontend against it. Each task has a bounded scope, dependencies, and completion criteria. Tasks within a phase may proceed in parallel only when their dependencies allow it.

Product requirements are in [spec.md](./spec.md), architecture decisions are in [plan.md](./plan.md), and the approved application layouts are in [backend-strucutre.md](./backend-strucutre.md) and [frontend-structure.md](./frontend-structure.md).

## Phase 0 — Resolve implementation-critical details

- [x] **Phase complete**

### T-001: Finalize week-boundary snapshot edge cases

- [x] **Task complete**

Clarify how week-boundary snapshots treat tasks or paths deleted before snapshot processing, and how timezone changes affect locked historical time entries and snapshots.

**Completion Criteria**

- Decisions cover deletions before snapshot processing.
- Decisions explain how locked time entries are regrouped after a timezone change.
- Rules preserve the requirement that finalized goal snapshots are immutable.

**Decisions**

- Snapshot reconstruction uses the state at the exact user-local week boundary. Records deleted after that boundary still contribute if they existed at the boundary.
- A path-specific goal deleted with its path before delayed processing still receives a historical snapshot when it existed at the boundary.
- Timezone changes regroup only entries in weeks that have not been finalized, using the new timezone. Entries may become locked if their recalculated week has ended.
- Finalized learning-time history and goal snapshots remain immutable across timezone changes.

### T-002: Verify crypto-erasure feasibility

- [x] **Task complete**

Design and verify the per-user encryption-key approach needed to make account data in backups unrecoverable immediately.

**Completion Criteria**

- A reviewed design specifies key creation, usage, destruction, failure behavior, and backup implications.
- Hosting and key-management provider requirements are recorded.
- Provider selection and production launch remain blocked until the required key-destruction capability is verified.

**Design decision**

- Use envelope encryption with a per-user DEK and a per-user KEK managed by the selected key-management provider. User-owned records and history are persisted as ciphertext; only wrapped DEKs and key metadata are durable.
- On deletion, block access first, destroy the KEK irreversibly, then delete live records and request Clerk identity deletion. Key-destruction failure is fail-closed: access stays blocked, the workflow reports failure and alerts operators, and retries are idempotent. Clerk failures retry independently without restoring data or keys.
- Backups and replicas may retain ciphertext during their retention period, but destruction of the KEK must make those copies computationally unrecoverable. Restoration must not recreate a deleted KEK or reactivate the account.
- Production remains blocked until a provider is verified to support immediate irreversible destruction across key versions, replicas, and provider-managed backups. Scheduled deletion, disablement, revocation, or a recovery window is insufficient.

## Phase 1 — Backend foundation

- [ ] **Phase complete**

### T-003: Scaffold the backend project

- [x] **Task complete**

Create the backend project root using the approved backend structure.

**Completion Criteria**

- The FastAPI application package, configuration, migration, and test locations are present.
- The backend can be installed and started independently.
- No product feature behavior is included.

### T-004: Configure backend settings and local development

- [ ] **Task complete**

Add environment-based settings, `API_PREFIX`, logging defaults, and local SQLite configuration.

**Depends on:** T-003

**Completion Criteria**

- The FastAPI application starts using environment-based configuration.
- `.env.example` documents required settings without exposing secrets.
- The configured API prefix is applied to API routes.

### T-005: Set up async database sessions and migrations

- [ ] **Task complete**

Configure async SQLAlchemy, `aiosqlite`, async session lifecycle, declarative metadata, and Alembic.

**Depends on:** T-004

**Completion Criteria**

- A migration can be generated and applied to an isolated local SQLite database.
- Development and test databases are separate.

### T-006: Establish backend test tooling

- [ ] **Task complete**

Configure pytest and isolated temporary SQLite databases for backend tests.

**Depends on:** T-005

**Completion Criteria**

- A representative async unit/API test runs locally.
- Test setup does not read from or modify development data.

### T-007: Verify Clerk tokens in the backend

- [ ] **Task complete**

Implement Clerk JWT verification and a dependency that exposes the authenticated user identity to protected routes.

**Depends on:** T-005

**Completion Criteria**

- Valid Clerk tokens resolve to the expected identity.
- Missing, invalid, expired, or incorrectly issued tokens are rejected in tests.
- Token values are never written to logs.

### T-008: Add user records and ownership scoping

- [ ] **Task complete**

Persist the Clerk subject and user timezone, and establish query patterns that scope user data to its owner.

**Depends on:** T-007

**Completion Criteria**

- The application can resolve or create a user record from a verified identity.
- API tests prove one user cannot read or modify another user's records.

### T-009: Define shared API errors and validation

- [ ] **Task complete**

Implement consistent API errors and shared validation behavior, including title length, URL length, and URL validity.

**Depends on:** T-004

**Completion Criteria**

- Invalid input produces predictable client errors.
- Tests cover titles over 100 characters, URLs over 2,048 characters, and invalid URLs.

## Phase 2 — Backend product APIs

- [ ] **Phase complete**

### T-010: Implement learning paths and stages

- [ ] **Task complete**

Add database models, migrations, schemas, services, and routes for paths and stages.

**Depends on:** T-008, T-009

**Completion Criteria**

- Users can create, view, edit, reorder, and delete their own paths and stages through the API.
- Sibling-title uniqueness is enforced.
- API tests cover validation and ownership.

### T-011: Implement tasks, statuses, and path completion

- [ ] **Task complete**

Add task management, ordering, status values, timestamped status history, and completion calculations.

**Depends on:** T-010

**Completion Criteria**

- Tasks support Not Started, In Progress, and Completed, including changing away from Completed.
- A path's completion is calculated from its tasks; a path without tasks returns N/A.
- Task status changes are timestamped for week-boundary reconstruction.
- API and service tests cover status and completion behavior.

### T-012: Implement links and path/stage deletion behavior

- [ ] **Task complete**

Support links attached to paths, stages, and tasks; implement the agreed cascade rules.

**Depends on:** T-010, T-011, T-013, T-014

**Completion Criteria**

- Links can be created, viewed, edited, and deleted at supported levels.
- Path deletion removes its descendants, links, time entries, and path-specific goals.
- Stage deletion removes its tasks and links but retains path-level time entries and path-specific goals.
- API behavior supports the required confirmation UX; destructive operations are covered by tests.

### T-013: Implement path-level learning-time tracking

- [ ] **Task complete**

Add dated learning-time entries, validation, week grouping, and history-lock behavior.

**Depends on:** T-008, T-010, T-001

**Completion Criteria**

- Users can add, view, edit, and delete their own entries while the entry's week is active.
- Entries must be greater than zero, at most 24 hours, and may be fractional.
- Multiple entries for the same path and week are allowed.
- Week grouping uses Saturday–Friday boundaries in the user's timezone.
- Entries assigned to ended weeks cannot be edited or deleted.
- Timezone changes follow the decision made in T-001.

### T-014: Implement weekly goals and active-week progress

- [ ] **Task complete**

Add overall and path-specific hour/task goals, progress calculation, and uniqueness rules.

**Depends on:** T-011, T-013

**Completion Criteria**

- Goals can be created and edited only for the current week.
- A path-specific task goal counts only completed tasks in that path.
- Progress is capped at 100%.
- At most one goal exists for each week/type/scope combination, enforced by application validation and a database constraint.
- API and service tests cover goal rules and progress calculations.

### T-015: Implement immutable goal snapshots and scheduled processing

- [ ] **Task complete**

Add snapshot persistence and the scheduled worker, reusing weekly-goal service logic.

**Depends on:** T-001, T-011, T-014

**Completion Criteria**

- The worker reconstructs goal progress as of the exact user-local Saturday–Friday boundary.
- A delayed or retried run produces exactly one snapshot per goal/week.
- Finalized snapshots are immutable.
- Required timestamped history is retained until the corresponding snapshot is finalized.
- Worker tests cover retries, duplicate invocations, and boundary calculations.

### T-016: Implement dashboard aggregation APIs

- [ ] **Task complete**

Provide weekly, monthly, and per-path statistics for the Dashboard.

**Depends on:** T-011, T-013, T-014, T-015

**Completion Criteria**

- API responses include total learning hours, path completion, task counts, goal progress, and weekly/monthly statistics.
- Weekly ranges use Saturday–Friday in the user's timezone; monthly ranges use calendar months.
- API tests cover empty data, current periods, and period navigation.

### T-017: Implement account deletion orchestration

- [ ] **Task complete**

Implement the idempotent account deletion workflow across access revocation, per-user key destruction, application records, and Clerk.

**Depends on:** T-002, T-008, T-010, T-011, T-013, T-014, T-015

**Completion Criteria**

- Account access is blocked immediately when deletion starts.
- The user's data key is destroyed and all live application records and history are removed.
- Clerk deletion failures can be retried safely without restoring user data.
- Operational failures generate an alert; logs exclude tokens, keys, and learning content.
- Tests cover success, retries, and partial external-service failures.

### T-018: Verify backend API contract and critical behavior

- [ ] **Task complete**

Review the complete OpenAPI contract and run the backend unit/API/worker tests against the approved requirements.

**Depends on:** T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-017

**Completion Criteria**

- OpenAPI operations, request/response schemas, auth requirements, and error responses are consistent.
- Critical backend requirements are covered: validation, ownership, deletion, time rules, week boundaries, goals, snapshots, and dashboard aggregation.
- All backend tests pass using an isolated temporary SQLite database.
- The API contract is ready for frontend implementation.

## Phase 3 — Frontend foundation and authentication

- [ ] **Phase complete**

### T-019: Scaffold the frontend application

- [ ] **Task complete**

Configure React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, and global providers.

**Depends on:** T-018

**Completion Criteria**

- The frontend builds and displays a basic responsive app shell.
- Application routes and providers are initialized.
- Environment configuration is documented without committing secrets.

### T-020: Establish frontend test tooling

- [ ] **Task complete**

Configure Vitest, React Testing Library, and shared frontend test helpers.

**Depends on:** T-019

**Completion Criteria**

- A representative component test runs locally.
- Test utilities support rendering the app with its required providers.

### T-021: Implement Clerk login and registration UI

- [ ] **Task complete**

Integrate Clerk login and registration pages with the agreed registration-to-login-to-Dashboard flow.

**Depends on:** T-019

**Completion Criteria**

- Email/password and Google flows are wired through Clerk.
- Registration returns the user to Login; successful sign-in leads to the Dashboard.
- Protected frontend routes require an authenticated session.

### T-022: Implement the authenticated API client and session-expiry recovery

- [ ] **Task complete**

Attach Clerk tokens to API requests and handle expired sessions in the frontend.

**Depends on:** T-021

**Completion Criteria**

- Authenticated API calls include a valid session token.
- On session expiry, the agreed message appears and the user is sent to Login.
- After login, the user returns to the requested page with unsaved form changes preserved.
- Frontend tests cover the expiry and recovery flow.

## Phase 4 — Frontend feature flows

- [ ] **Phase complete**

### T-023: Implement learning-path management UI

- [ ] **Task complete**

Build path, stage, task, and link pages/forms, including search, filtering, sorting, reordering, empty states, validation, and delete confirmations.

**Depends on:** T-022

**Completion Criteria**

- Users can complete the path-management journey through the UI and backend API.
- Path and stage deletion behavior matches the approved cascade rules.
- Forms show API validation errors and empty states guide users to create their first item.

### T-024: Implement learning-time UI

- [ ] **Task complete**

Build path selection, time-entry management, and selected-week display/navigation.

**Depends on:** T-022

**Completion Criteria**

- Users can add, view, edit, and delete eligible entries from the UI.
- Invalid hour values receive clear feedback.
- Ended-week entries are presented as read-only.
- Displayed week boundaries match the user's timezone.

### T-025: Implement weekly-goals UI

- [ ] **Task complete**

Build current-week goal creation/editing and historical goal viewing.

**Depends on:** T-022

**Completion Criteria**

- Users can create or edit goals only for the current week.
- Other weeks are view-only and show frozen snapshots.
- Duplicate-goal validation and progress capped at 100% are reflected in the UI.

### T-026: Implement Dashboard UI

- [ ] **Task complete**

Build Dashboard metrics, charts, current-week default, and period navigation.

**Depends on:** T-022

**Completion Criteria**

- Dashboard shows hours, path completion, completed/incomplete tasks, goals, and weekly/monthly statistics.
- It defaults to the current Saturday–Friday week and supports period navigation.
- Empty states and loading/error states are accessible and understandable.

## Phase 5 — Frontend verification and release readiness

- [ ] **Phase complete**

### T-027: Add critical frontend tests

- [ ] **Task complete**

Cover critical user-visible behaviors with Vitest and React Testing Library.

**Depends on:** T-023, T-024, T-025, T-026

**Completion Criteria**

- Tests cover forms, validation, task status changes, empty states, goal progress, and session-expiry recovery.
- No minimum code-coverage percentage is required.

### T-028: Add focused end-to-end browser journeys

- [ ] **Task complete**

Configure Playwright journeys for authentication and a core learning-path/task/goal flow.

**Depends on:** T-021, T-023, T-024, T-025, T-026

**Completion Criteria**

- Critical journeys pass locally with external services mocked where appropriate.
- A controlled smoke test for the real Clerk integration is documented and can be run separately.

### T-029: Verify accessibility, responsiveness, and performance

- [ ] **Task complete**

Validate the core user flows against the approved accessibility, device, and performance targets.

**Depends on:** T-027, T-028

**Completion Criteria**

- Core flows support keyboard navigation, visible focus, labeled controls, readable contrast, and accessible status/error announcements.
- Core screens work at desktop and mobile viewport sizes.
- Production-like measurement meets the agreed Core Web Vitals and API response-time targets.

### T-030: Migrate production deployment to PostgreSQL

- [ ] **Task complete**

Configure managed PostgreSQL and apply Alembic migrations; add PostgreSQL-backed integration tests during the migration.

**Depends on:** T-005, T-018

**Completion Criteria**

- The API and worker operate against PostgreSQL using `asyncpg`.
- Alembic migrations apply successfully to a clean PostgreSQL database.
- Critical integration tests pass against PostgreSQL.

### T-031: Complete hosting and operational readiness

- [ ] **Task complete**

Select managed hosting and key management; configure secrets, HTTPS, CORS, worker scheduling, monitoring, and deletion-safe backup procedures.

**Depends on:** T-002, T-015, T-017, T-030

**Completion Criteria**

- Provider capabilities satisfy the crypto-erasure requirement.
- A production-like deployment runs the web app, API, database, and worker.
- Operational alerts and account-deletion failure handling are verified.
- Backup restoration procedures cannot restore deleted users' recoverable data.

## Sequencing Notes

- The workflow is backend-first: finish the backend API and its critical SQLite tests before scaffolding the frontend.
- T-001 and T-002 are implementation/design prerequisites for snapshots and deletion. Backend scaffolding can proceed while these are being resolved.
- Once the backend API contract is reviewed in T-018, frontend work proceeds against that contract.
- SQLite is the initial development and test database. PostgreSQL-backed integration tests are added during the production database migration.
- Tests are run locally for now. Pull-request CI automation remains undecided and is not included as a required task.
- Deferred features—including AI, sharing, notifications, data export, archiving, and stage/task-level time tracking—are not part of this implementation plan.
