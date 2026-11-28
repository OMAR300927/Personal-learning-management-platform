import { Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../auth/ProtectedRoute'
import { SessionExpiryHandler } from '../auth/SessionExpiryHandler'
import { AppLayout } from '../layouts/AppLayout'
import { AuthLayout } from '../layouts/AuthLayout'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { RegisterPage } from '../features/auth/pages/RegisterPage'
import { RegistrationCompletePage } from '../features/auth/pages/RegistrationCompletePage'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'
import { LearningPathsPage } from '../features/learning-paths/pages/LearningPathsPage'
import { LearningTimePage } from '../features/learning-time/pages/LearningTimePage'
import { WeeklyGoalsPage } from '../features/weekly-goals/pages/WeeklyGoalsPage'

/** Maps public authentication and protected product pages to their layouts. */
export function AppRouter() {
  return (
    <>
      <SessionExpiryHandler />
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="login/*" element={<LoginPage />} />
          <Route path="register/*" element={<RegisterPage />} />
          <Route
            path="registration-complete"
            element={<RegistrationCompletePage />}
          />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="learning-paths" element={<LearningPathsPage />} />
            <Route path="learning-time" element={<LearningTimePage />} />
            <Route path="weekly-goals" element={<WeeklyGoalsPage />} />
          </Route>
        </Route>
        <Route
          path="*"
          element={<p className="p-8 text-center">Page not found</p>}
        />
      </Routes>
    </>
  )
}
