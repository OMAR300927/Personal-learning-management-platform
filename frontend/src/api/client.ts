import { ApiError, createApiError } from './errors'

interface ApiClientOptions {
  baseUrl: string | undefined
  getToken: () => Promise<string | null>
  onUnauthorized: () => void
  fetcher?: (
    input: RequestInfo | URL,
    init?: RequestInit,
  ) => Promise<Response>
}

export function createApiClient({
  baseUrl,
  getToken,
  onUnauthorized,
  fetcher = fetch,
}: ApiClientOptions) {
  /** Sends an authenticated request and decodes its successful response. */
  async function request<T>(
    path: string,
    decode: (payload: unknown) => T,
    init: RequestInit = {},
  ): Promise<T> {
    if (!baseUrl) {
      throw new Error(
        'API is not configured. Set VITE_API_BASE_URL in frontend/.env.',
      )
    }

    const token = await getToken()
    if (!token) {
      onUnauthorized()
      throw new ApiError('Authentication is required.', 401, 'unauthorized')
    }

    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${token}`)
    headers.set('Accept', 'application/json')

    const response = await fetcher(
      `${baseUrl.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`,
      { ...init, headers },
    )

    if (response.status === 401) {
      onUnauthorized()
    }

    const payload: unknown =
      response.status === 204 ? undefined : await response.json()

    if (!response.ok) {
      throw createApiError(response.status, payload)
    }

    return decode(payload)
  }

  return { request }
}
