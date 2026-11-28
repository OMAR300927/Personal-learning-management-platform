import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { SessionExpiryHandler } from './SessionExpiryHandler'
import { SESSION_EXPIRED_EVENT } from './session-expiry'

const clerkMock = vi.hoisted(() => ({
  signOut: vi.fn(),
}))

vi.mock('@clerk/react', () => ({
  useAuth: () => ({ isLoaded: true, isSignedIn: false }),
  useClerk: () => clerkMock,
  useSignIn: () => ({
    errors: {
      fields: { identifier: null, password: null, code: null },
      global: null,
      raw: null,
    },
  }),
  SignIn: ({ forceRedirectUrl }: { forceRedirectUrl?: string }) => (
    <output data-testid="sign-in-redirect">{forceRedirectUrl}</output>
  ),
}))

describe('SessionExpiryHandler', () => {
  beforeEach(() => {
    clerkMock.signOut.mockReset()
    clerkMock.signOut.mockResolvedValue(undefined)
  })

  it('shows the required message and returns to the interrupted route after login', async () => {
    render(
      <MemoryRouter initialEntries={['/learning-paths?filter=active']}>
        <SessionExpiryHandler />
        <Routes>
          <Route path="/learning-paths" element={<p>Learning paths</p>} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent(window, new Event(SESSION_EXPIRED_EVENT))

    expect(
      await screen.findByText('Your session has expired. Please log in.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(clerkMock.signOut).toHaveBeenCalledOnce())
    expect(screen.getByTestId('sign-in-redirect')).toHaveTextContent(
      '/learning-paths?filter=active',
    )
  })
})
