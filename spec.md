# Personal Learning Management Platform

## 1. Product Overview and Goals

The Personal Learning Management Platform helps individuals organize learning paths, manage learning tasks, record learning time, and set weekly learning goals.

The MVP aims to:

- Give each user a private place to manage their learning.
- Make learning progress and time visible through a dashboard.
- Support consistent weekly planning and review.
- Provide a responsive, desktop-first experience.

## 2. MVP Scope

### In scope

- Clerk authentication with email/password and Google.
- Account deletion.
- Dashboard.
- Learning path, stage, task, and link management.
- Task status and learning path completion.
- Path-level learning-time tracking.
- Weekly goals for learning hours and completed tasks.
- Weekly and monthly statistics.
- Search, filtering, sorting, and manual ordering.
- Responsive interface, empty states, and basic accessibility.

### Out of scope for the MVP

- Public sharing, teams, or collaboration.
- AI-generated paths, plans, progress analysis, or recommendations.
- Notifications and reminders.
- Data export.
- Stage archiving.
- Learning-time entries assigned to stages or tasks.
- Multiple languages.

## 3. Functional Requirements

### 3.1 Accounts and sessions

- **FR-1:** Users can register and sign in through Clerk using email/password or Google.
- **FR-2:** If a user at Login needs an account, the application directs them to Register. After successful registration, the user is redirected to Login and must sign in before accessing the Dashboard. Email verification is not required.
- **FR-3:** Users can access only their own application data.
- **FR-4:** Users can permanently delete their account and all associated data immediately.
- **FR-5:** When a session expires, the application displays: “Your session has expired. Please log in.” It redirects the user to login and, after successful login, returns them to the originally requested page.
- **FR-6:** Unsaved form changes are preserved across the session-expiry login flow.
- **FR-7:** Session expiry behavior follows Clerk's configured session behavior.

### 3.2 Learning paths, stages, tasks, and links

- **FR-8:** Users can create, view, edit, reorder, and delete learning paths.
- **FR-9:** A learning path can contain stages. Stages can contain tasks.
- **FR-10:** Users can create, view, edit, reorder, and delete stages and tasks.
- **FR-11:** Users can attach links to a learning path, stage, or task.
- **FR-12:** Task statuses are Not Started, In Progress, and Completed. Users can change a task from Completed to another status.
- **FR-13:** A path's completion is based on its completed tasks. If it has no tasks, its completion is displayed as N/A.
- **FR-14:** Titles are unique among sibling items.
- **FR-15:** Users can search, filter, and sort applicable lists.
- **FR-16:** Deleting a path requires confirmation and irreversibly deletes the path, its stages, tasks, links, path-level learning-time entries, and path-specific goals.
- **FR-17:** Deleting a stage requires confirmation and irreversibly deletes the stage, its tasks, and links. It retains path-level learning-time entries and path-specific goals.
- **FR-18:** Tasks cannot be moved between paths or stages in the MVP.
- **FR-19:** Empty pages provide prompts to create the first relevant path, task, or goal.

### 3.3 Learning-time tracking

- **FR-20:** Users can create, edit, and delete learning-time entries associated with a learning path.
- **FR-21:** Entries are recorded for Saturday–Friday weeks, using the user's timezone.
- **FR-22:** A user can record multiple entries for the same path and week.
- **FR-23:** An entry must be greater than zero, may be fractional, and cannot exceed 24 hours.
- **FR-24:** Learning-time entries are associated with paths only, not stages or tasks.
- **FR-25:** If a user's timezone changes, existing week boundaries are recalculated.

### 3.4 Weekly goals

- **FR-26:** Users can create and edit fixed-week goals for learning hours or completed-task counts for the current week only.
- **FR-27:** A goal can apply to the user's learning overall or to one learning path.
- **FR-28:** A path-specific task goal counts only tasks in that path.
- **FR-29:** During the active week, task-goal progress counts tasks currently marked Completed.
- **FR-30:** When a week ends, its goal progress is frozen and an unfinished goal remains visible as incomplete in history.
- **FR-31:** Goal progress is capped at 100%.
- **FR-32:** The Weekly Goals page shows goal progress and total learning hours across all weeks. Users can select other weeks to view goal history, but cannot create or edit goals for past or future weeks.
- **FR-38:** For each week, users can have at most one goal of each type and scope (for example, one overall hours goal and one hours goal for each individual path).

### 3.5 Dashboard and reporting

- **FR-33:** The Dashboard shows total learning hours, completion for each path, and completed and incomplete task counts.
- **FR-34:** The Dashboard shows progress toward weekly goals and weekly and monthly statistics.
- **FR-35:** The Dashboard defaults to the current Saturday–Friday week.
- **FR-36:** Users can navigate to previous and next weeks and months.
- **FR-37:** Monthly statistics use calendar months.

## 4. Business Rules

- **BR-1:** All learning data belongs to one user and is private to that user.
- **BR-2:** A task has one of the three defined statuses. Completed tasks may be changed back to another status.
- **BR-3:** Path completion is calculated from completed tasks divided by all tasks. A path with no tasks has no applicable percentage and displays N/A.
- **BR-4:** Incomplete task counts include tasks marked Not Started or In Progress.
- **BR-5:** Learning time is recorded at path level and grouped into Saturday–Friday weeks in the user's timezone.
- **BR-6:** An individual time entry must be greater than zero and at most 24 hours. Multiple entries for the same path and week are allowed.
- **BR-7:** Weekly goals target a fixed amount of learning hours or a fixed count of completed tasks.
- **BR-8:** A path-specific task goal counts completed tasks in that path only.
- **BR-9:** Active-week task-goal progress reflects current task statuses. Once the week ends, its progress is frozen.
- **BR-10:** Goal progress cannot exceed 100%. Unfinished goals remain incomplete in historical views.
- **BR-11:** Changing a user's timezone recalculates existing week boundaries.
- **BR-12:** Path and stage deletion are irreversible. A path deletion removes its associated path-specific goals; stage deletion retains those goals and path-level time entries.
- **BR-13:** Goals can be created or edited only for the current week. Other weeks are available for viewing history only.
- **BR-14:** A week can have at most one goal for each combination of goal type and scope.

## 5. Non-Functional Requirements

### Usability and accessibility

- **NFR-1:** The interface is desktop-first and responsive on mobile devices.
- **NFR-2:** Target WCAG 2.2 AA as the design and testing standard. This is a target, not a certification requirement.
- **NFR-3:** Core flows support keyboard navigation, visible focus, labeled controls, readable contrast, and accessible error and status announcements.
- **NFR-4:** The MVP interface is in English.

### Performance and scale

- **NFR-5:** At least 75% of measured visits should meet these Core Web Vitals targets:
  - Largest Contentful Paint (LCP) at or below 2.5 seconds.
  - Interaction to Next Paint (INP) at or below 200 milliseconds.
  - Cumulative Layout Shift (CLS) at or below 0.1.
- **NFR-6:** Common API requests should have a 95th-percentile response time at or below 500 milliseconds under expected MVP load.
- **NFR-7:** The MVP is expected to support thousands of users.
- **NFR-8:** Performance targets are measured on production-like infrastructure and representative data.

### Privacy and data integrity

- **NFR-9:** Authentication and session management use Clerk.
- **NFR-10:** Backend access checks enforce data ownership for every user-specific operation.
- **NFR-11:** Account deletion immediately blocks access and removes the user's live application data. Encrypted backups may retain data until their documented retention period expires; restore procedures must replay an independent deletion ledger before making restored data accessible.
- **NFR-12:** Data changes and cascading deletions do not leave orphaned or cross-account records.

## 6. Constraints and Approved Assumptions

### Constraints

- Backend: FastAPI.
- Frontend: React.
- Development database: SQLite.
- Production database: PostgreSQL.
- Styling: Tailwind CSS.
- Charts: Recharts.
- Icons: Lucide React.
- Authentication: Clerk.
- The MVP is desktop-first, responsive, and English-only.

### Approved assumptions

- Maximum title length: **100 characters**.
- Maximum URL length: **2,048 characters**.
- URLs must be validated before saving.
- These field limits may be revised later if product needs require it.
- The performance and accessibility targets in this specification are accepted product targets.

## 7. Acceptance Criteria

### Accounts and sessions

- **AC-1:** A user who needs an account from Login is directed to Register. After successful registration, the user lands on Login; after signing in using email/password or Google, the user lands on the Dashboard. Email verification is not required.
- **AC-2:** Attempts to read or change another user's records are denied.
- **AC-3:** Confirming account deletion immediately blocks access, deletes live application data, and requests Clerk identity deletion with safe retries. Encrypted backups expire automatically according to the documented retention policy, and the independent deletion ledger is replayed after backup restoration before the application becomes accessible.
- **AC-4:** On session expiry, the exact agreed message is displayed; the user is sent to login, returned to the requested page after login, and their unsaved form changes are preserved.

### Learning data

- **AC-5:** A user can create, view, edit, reorder, and delete paths, stages, and tasks, and attach links at each supported level.
- **AC-6:** Sibling items cannot be saved with duplicate titles. Titles over 100 characters and URLs over 2,048 characters are rejected with a clear validation message.
- **AC-7:** Tasks can be set to each of the three statuses, including changing a Completed task back to another status.
- **AC-8:** Path completion reflects completed tasks; a path with no tasks displays N/A.
- **AC-9:** Deleting a path prompts for confirmation and removes its stages, tasks, links, time entries, and path-specific goals.
- **AC-10:** Deleting a stage prompts for confirmation and removes that stage, its tasks, and links, while retaining path-level time entries and path-specific goals.
- **AC-11:** Search, filtering, sorting, and manual ordering work on applicable lists. Tasks cannot be moved between paths or stages.
- **AC-12:** Empty pages display a prompt to create the first relevant item.

### Learning time and goals

- **AC-13:** A user can add, edit, and delete path-level learning-time entries. Entries support fractional hours, reject values at or below zero and above 24, and allow multiple entries for the same path and week.
- **AC-14:** Week grouping uses Saturday–Friday boundaries in the user's timezone. Changing the timezone recalculates existing week boundaries.
- **AC-15:** A user can create and edit overall or path-specific weekly goals for hours or completed-task counts for the current week only. The system prevents more than one goal for the same type and scope in a week.
- **AC-16:** A path-specific task goal counts only completed tasks in that path; active-week progress reflects their current statuses.
- **AC-17:** Goal progress is capped at 100%. At week end, progress is frozen and unfinished goals remain visible as incomplete in history.
- **AC-18:** The Weekly Goals page shows goal progress and total learning hours across all weeks. Users can view other weeks' goal history but cannot create or edit goals for those weeks.

### Dashboard

- **AC-19:** The Dashboard displays total learning hours, per-path completion, completed and incomplete task counts, goal progress, and weekly and monthly statistics.
- **AC-20:** The Dashboard initially shows the current Saturday–Friday week. Users can navigate between weeks and months, and monthly figures use calendar months.

### Quality targets

- **AC-21:** Core screens are usable at desktop and mobile viewport sizes, and core flows meet the stated keyboard, focus, labeling, contrast, and status-announcement accessibility criteria.
- **AC-22:** In performance measurement on production-like infrastructure and representative data, at least 75% of visits meet the stated LCP, INP, and CLS targets, and common API requests meet the stated p95 target.

## 8. Testing

### Test approach

- **TEST-1:** Backend unit and API tests use pytest.
- **TEST-2:** Backend tests use an isolated temporary test database and must not read from or modify development data.
- **TEST-3:** Frontend unit and component tests use Vitest and React Testing Library.
- **TEST-4:** A focused Playwright suite covers critical end-to-end browser journeys.
- **TEST-5:** Routine automated tests mock or stub external services. A controlled smoke test verifies the real Clerk integration.
- **TEST-6:** Tests prioritize critical behaviors and acceptance criteria. No minimum code-coverage percentage is required initially.
- **TEST-7:** Tests are run locally for now. Automated pull-request execution has not been decided.

### Testing acceptance criteria

- **TAC-1:** Backend tests cover critical API behavior, including validation, per-user data isolation, deletion, time-entry rules, week boundaries, and goal progress.
- **TAC-2:** Frontend tests cover critical user-visible behavior, including forms and validation, task status changes, empty states, goal progress, and session-expiry messaging and recovery.
- **TAC-3:** Playwright tests exercise a focused set of critical browser journeys, including a core learning-path/task/goal flow.
- **TAC-4:** Routine automated tests do not depend on live external services; the real Clerk smoke test runs in a controlled environment.
- **TAC-5:** Backend test runs use an isolated temporary database.

## 9. Future Features

The following are deferred possibilities, not commitments for the first release:

- AI assistance to create learning paths.
- AI progress analysis, weakness identification, and recommendations.
- Automatically generated learning plans, estimated hours, or completion projections.
- Public sharing, private links, teams, or collaboration.
- Goal reminders and notifications.
- Data export.
- Stage archiving.
- Stage- or task-level time tracking.
- Support for additional languages.
