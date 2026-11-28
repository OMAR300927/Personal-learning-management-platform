import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RegistrationCompletePage } from './RegistrationCompletePage'

const clerkMock = vi.hoisted(() => ({
  isSignedIn: true,
  externalProviders: [] as string[],
  signOut: vi.fn(),
}))

vi.mock('@clerk/react', () => ({
  useAuth: () => ({ isLoaded: true, isSignedIn: clerkMock.isSignedIn }),
  useClerk: () => clerkMock,
  useUser: () => ({
    isLoaded: true,
    user: {
      externalAccounts: clerkMock.externalProviders.map((provider) => ({
        provider,
      })),
    },
  }),
}))

/** Renders registration completion with destinations for home and sign-in. */
function renderCompletionRoute() {
  return render(
    <MemoryRouter initialEntries={['/registration-complete']}>
      <Routes>
        <Route
          path="/registration-complete"
          element={<RegistrationCompletePage />}
        />
        <Route path="/" element={<p>Home</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RegistrationCompletePage', () => {
  beforeEach(() => {
    clerkMock.isSignedIn = true
    clerkMock.externalProviders = []
    clerkMock.signOut.mockReset()
    clerkMock.signOut.mockResolvedValue(undefined)
  })

  it('keeps Google registrations signed in and sends them home', async () => {
    clerkMock.externalProviders = ['google']

    renderCompletionRoute()

    expect(await screen.findByText('Home')).toBeInTheDocument()
    expect(clerkMock.signOut).not.toHaveBeenCalled()
  })

  it('signs out email registrations and returns them to login', async () => {
    renderCompletionRoute()

    expect(await screen.findByText('Login')).toBeInTheDocument()
    expect(clerkMock.signOut).toHaveBeenCalledOnce()
  })
})
