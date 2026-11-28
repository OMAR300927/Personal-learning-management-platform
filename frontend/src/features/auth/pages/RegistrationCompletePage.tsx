import { useAuth, useClerk, useUser } from '@clerk/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

/** Sends Google registrations home and returns email registrations to sign-in. */
export function RegistrationCompletePage() {
  const { isLoaded, isSignedIn } = useAuth()
  const { isLoaded: isUserLoaded, user } = useUser()
  const clerk = useClerk()
  const navigate = useNavigate()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const isGoogleAccount =
    user?.externalAccounts.some(({ provider }) => provider === 'google') ?? false

  useEffect(() => {
    if (!isLoaded || !isUserLoaded) {
      return
    }

    let isMounted = true

    /** Completes Google registration at home and returns email users to sign-in. */
    async function finishRegistration() {
      if (isSignedIn && isGoogleAccount) {
        navigate('/', { replace: true })
        return
      }

      if (isSignedIn) {
        await clerk.signOut()
      }

      if (isMounted) {
        navigate('/login?registered=1', { replace: true })
      }
    }

    void finishRegistration().catch((error: unknown) => {
      if (isMounted) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : 'Could not finish registration. Please try signing in.',
        )
      }
    })

    return () => {
      isMounted = false
    }
  }, [clerk, isGoogleAccount, isLoaded, isSignedIn, isUserLoaded, navigate])

  if (errorMessage) {
    return (
      <div role="alert" className="text-sm leading-6 text-rose-200">
        {errorMessage}
      </div>
    )
  }

  return (
    <p role="status" className="text-sm text-slate-300">
      {isSignedIn && isGoogleAccount
        ? 'Google registration complete. Taking you home…'
        : 'Registration complete. Taking you to sign in…'}
    </p>
  )
}
