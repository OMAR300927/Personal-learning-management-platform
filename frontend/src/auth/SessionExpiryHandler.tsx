import { useClerk } from '@clerk/react'
import { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { clearAuthenticatedSession, SESSION_EXPIRED_EVENT } from './session-expiry'

/** Provides a safe message when Clerk cannot close an expired session. */
function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : 'Your session could not be closed. Please try signing in again.'
}

/** Signs out on expiry events and returns the user to the login page. */
export function SessionExpiryHandler() {
  const { signOut } = useClerk()
  const location = useLocation()
  const navigate = useNavigate()
  const isHandlingExpiry = useRef(false)

  useEffect(() => {
    /** Closes the current session and preserves the route being interrupted. */
    function handleSessionExpired() {
      if (isHandlingExpiry.current || location.pathname === '/login') {
        return
      }

      isHandlingExpiry.current = true
      const from = `${location.pathname}${location.search}${location.hash}`

      void signOut()
        .then(() => {
          clearAuthenticatedSession()
          navigate('/login', {
            replace: true,
            state: { from, sessionExpired: true },
          })
        })
        .catch((error: unknown) => {
          clearAuthenticatedSession()
          navigate('/login', {
            replace: true,
            state: {
              from,
              sessionExpired: true,
              signOutError: errorMessage(error),
            },
          })
        })
        .finally(() => {
          isHandlingExpiry.current = false
        })
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
    return () =>
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
  }, [location.hash, location.pathname, location.search, navigate, signOut])

  return null
}
