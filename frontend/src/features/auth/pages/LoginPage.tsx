import { SignIn, useAuth, useSignIn } from '@clerk/react'
import { Navigate, useLocation, useSearchParams } from 'react-router-dom'
import { authAppearance } from '../components/appearance'
import {
  isUnknownEmailError,
  unknownAccountMessage,
} from '../../../auth/unknown-account'

/** Renders Clerk sign-in and restores the route interrupted by session expiry. */
export function LoginPage() {
  const { isLoaded, isSignedIn } = useAuth()
  const { errors } = useSignIn()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const showUnknownEmailMessage = isUnknownEmailError(errors)
  const loginState = location.state as
    | { from?: unknown; sessionExpired?: boolean; signOutError?: string }
    | null
  const requestedPath = loginState?.from
  const sessionExpired = loginState?.sessionExpired === true
  const redirectUrl =
    typeof requestedPath === 'string' &&
    requestedPath.startsWith('/') &&
    !requestedPath.startsWith('//')
      ? requestedPath
      : '/'

  if (isLoaded && isSignedIn && !sessionExpired) {
    return <Navigate to="/" replace />
  }

  return (
    <div>
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-emerald-300">
        Welcome back
      </p>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
        Sign in to your account
      </h2>
      <p className="mt-2 mb-7 text-sm leading-6 text-slate-400">
        Pick up where you left off and keep your learning moving.
      </p>
      {searchParams.get('registered') === '1' && (
        <p
          role="status"
          className="mb-5 rounded-xl border border-emerald-300/20 bg-emerald-300/10 px-4 py-3 text-sm text-emerald-100"
        >
          Registration complete. Sign in to continue.
        </p>
      )}
      {sessionExpired && (
        <p
          role="alert"
          className="mb-5 rounded-xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-100"
        >
          Your session has expired. Please log in.
        </p>
      )}
      {loginState?.signOutError && (
        <p
          role="alert"
          className="mb-5 rounded-xl border border-rose-300/20 bg-rose-300/10 px-4 py-3 text-sm text-rose-100"
        >
          {loginState.signOutError}
        </p>
      )}
      {showUnknownEmailMessage && (
        <p
          role="alert"
          className="mb-5 rounded-xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-100"
        >
          {unknownAccountMessage}
        </p>
      )}
      <SignIn
        routing="path"
        path="/login"
        signUpUrl="/register"
        withSignUp={false}
        transferable
        forceRedirectUrl={redirectUrl}
        signUpForceRedirectUrl="/"
        appearance={authAppearance}
      />
    </div>
  )
}
