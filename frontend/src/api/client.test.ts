import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from './client'

describe('createApiClient', () => {
  it('attaches a Clerk bearer token to API requests', async () => {
    let authorizationHeader: string | null = null
    const client = createApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      getToken: async () => 'clerk-session-token',
      onUnauthorized: vi.fn(),
      fetcher: async (_input, init) => {
        authorizationHeader = new Headers(init?.headers).get('Authorization')
        return new Response(JSON.stringify({ ok: true }), { status: 200 })
      },
    })

    await client.request('/users/me', (payload) => payload)

    expect(authorizationHeader).toBe('Bearer clerk-session-token')
  })

  it('notifies the app and surfaces the API error when a request is unauthorized', async () => {
    const onUnauthorized = vi.fn()
    const client = createApiClient({
      baseUrl: 'http://localhost:8000/api/v1',
      getToken: async () => 'expired-session-token',
      onUnauthorized,
      fetcher: async () =>
        new Response(
          JSON.stringify({
            error: {
              code: 'http_error',
              message: 'Invalid authentication credentials',
            },
          }),
          { status: 401 },
        ),
    })

    await expect(
      client.request('/users/me', (payload) => payload),
    ).rejects.toMatchObject({
      message: 'Invalid authentication credentials',
      status: 401,
      code: 'http_error',
    })
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })
})
