import { useAuth } from '@clerk/react'
import { useMemo } from 'react'
import { createApiClient } from '../api/client'
import { notifySessionExpired } from '../auth/session-expiry'

/** Binds the API client to Clerk's token getter and session-expiry handler. */
export function useApiClient() {
  const { getToken } = useAuth()

  return useMemo(
    () =>
      createApiClient({
        baseUrl: import.meta.env.VITE_API_BASE_URL,
        getToken,
        onUnauthorized: notifySessionExpired,
      }),
    [getToken],
  )
}
