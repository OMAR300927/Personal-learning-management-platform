import { SignUp, useAuth } from '@clerk/react'
import { Navigate } from 'react-router-dom'
import { authAppearance } from '../components/appearance'

/** Renders Clerk registration and sends successful sign-ups through login. */
export function RegisterPage() {
  const { isLoaded, isSignedIn } = useAuth()

  if (isLoaded && isSignedIn) {
    return <Navigate to="/" replace />
  }

  return (
    <div>
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-emerald-300">
        Start learning
      </p>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
        Create your account
      </h2>
      <p className="mt-2 mb-7 text-sm leading-6 text-slate-400">
        Create an account with email, or continue with Google.
      </p>
      <SignUp
        routing="path"
        path="/register"
        signInUrl="/login"
        signInForceRedirectUrl="/"
        forceRedirectUrl="/registration-complete"
        appearance={authAppearance}
      />
    </div>
  )
}
