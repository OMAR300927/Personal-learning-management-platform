# Frontend Folder and File Structure

```text
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── .env.example
├── public/
└── src/
    ├── main.tsx
    ├── app/
    │   ├── App.tsx
    │   ├── router.tsx
    │   └── providers.tsx
    ├── api/
    │   ├── client.ts
    │   └── errors.ts
    ├── auth/
    │   ├── ClerkProvider.tsx
    │   ├── ProtectedRoute.tsx
    │   └── session-expiry.ts
    ├── layouts/
    │   ├── AppLayout.tsx
    │   └── AuthLayout.tsx
    ├── features/
    │   ├── auth/
    │   │   ├── pages/
    │   │   │   ├── LoginPage.tsx
    │   │   │   └── RegisterPage.tsx
    │   │   └── components/
    │   ├── dashboard/
    │   │   ├── pages/
    │   │   │   └── DashboardPage.tsx
    │   │   ├── components/
    │   │   └── hooks/
    │   ├── learning-paths/
    │   │   ├── pages/
    │   │   │   ├── LearningPathsPage.tsx
    │   │   │   └── LearningPathDetailPage.tsx
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   └── types.ts
    │   ├── learning-time/
    │   │   ├── pages/
    │   │   │   └── LearningTimePage.tsx
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   └── types.ts
    │   └── weekly-goals/
    │       ├── pages/
    │       │   └── WeeklyGoalsPage.tsx
    │       ├── components/
    │       ├── hooks/
    │       └── types.ts
    ├── components/
    │   ├── ui/
    │   └── feedback/
    ├── hooks/
    ├── lib/
    │   ├── date-week.ts
    │   └── validation.ts
    ├── styles/
    │   └── index.css
    └── test/
        ├── setup.ts
        └── test-utils.tsx

e2e/
├── playwright.config.ts
└── journeys/
    ├── authentication.spec.ts
    └── learning-path-goal.spec.ts
```

## Responsibilities

- `app/` assembles application providers and routes.
- `api/` handles HTTP requests and shared API errors. Authenticated requests attach the Clerk token.
- `auth/` contains frontend authentication integration, protected-route behavior, and session-expiry recovery.
- `features/` owns page-specific components and data hooks, organized around product features.
- `components/ui/` contains reusable, product-independent UI components. Feature-specific UI stays within its feature.
- `lib/` contains small shared utilities, including Saturday–Friday date calculations.
- `test/` configures Vitest and shared React test helpers. Component tests may be colocated with the components they cover.
- `e2e/` contains a focused set of Playwright user journeys.
