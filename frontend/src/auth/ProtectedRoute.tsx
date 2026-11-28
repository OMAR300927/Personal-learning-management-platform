import { useAuth } from '@clerk/react'
import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import {
  clearAuthenticatedSession,
  hasAuthenticatedSession,
  markAuthenticatedSession,
} from './session-expiry'

/** Protects nested routes and preserves the requested URL for login recovery. */
export function ProtectedRoute() {
  const { isLoaded, isSignedIn } = useAuth()
  const location = useLocation()
  const sessionExpired = isSignedIn || hasAuthenticatedSession()

  useEffect(() => {
    if (!isLoaded) {
      return
    }

    if (isSignedIn) {
      markAuthenticatedSession()
    } else {
      clearAuthenticatedSession()
    }
  }, [isLoaded, isSignedIn])

  if (!isLoaded) {
    return (
      <p role="status" className="p-8 text-center text-slate-300">
        Checking your session…
      </p>
    )
  }

  if (!isSignedIn) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: `${location.pathname}${location.search}${location.hash}`,
          ...(sessionExpired ? { sessionExpired: true } : {}),
        }}
      />
    )
  }

  return <Outlet />
}
