import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'

const authState = vi.hoisted(() => ({
  isLoaded: true,
  isSignedIn: false,
}))

vi.mock('@clerk/react', () => ({
  useAuth: () => authState,
}))

/** Displays login navigation state so redirect behavior can be asserted. */
function LoginTarget() {
  const location = useLocation()
  return <p>{JSON.stringify(location.state)}</p>
}

/** Renders the protected route from a chosen in-memory URL. */
function renderProtectedRoute(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/learning-paths" element={<p>Private learning paths</p>} />
        </Route>
        <Route path="/login" element={<LoginTarget />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    authState.isLoaded = true
    authState.isSignedIn = false
    window.sessionStorage.clear()
  })

  it('redirects signed-out users to login and remembers the requested route', () => {
    renderProtectedRoute('/learning-paths?filter=active')

    expect(screen.getByText('{"from":"/learning-paths?filter=active"}')).toBeInTheDocument()
  })

  it('shows protected content to signed-in users', () => {
    authState.isSignedIn = true

    renderProtectedRoute('/learning-paths')

    expect(screen.getByText('Private learning paths')).toBeInTheDocument()
  })

  it('waits for Clerk to load the session before redirecting', () => {
    authState.isLoaded = false

    renderProtectedRoute('/learning-paths')

    expect(screen.getByRole('status')).toHaveTextContent('Checking your session')
    expect(screen.queryByText('{"from":"/learning-paths"}')).not.toBeInTheDocument()
  })
})
