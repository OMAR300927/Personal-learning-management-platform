import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { unknownAccountMessage } from '../../../auth/unknown-account'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'

const clerkMock = vi.hoisted(() => ({
  identifierError: null as { code: string; message: string } | null,
  passwordError: null as { code: string; message: string } | null,
  globalErrorCodes: [] as string[],
}))

vi.mock('@clerk/react', () => ({
  SignIn: ({
    transferable,
    withSignUp,
    signUpForceRedirectUrl,
  }: {
    transferable?: boolean
    withSignUp?: boolean
    signUpForceRedirectUrl?: string
  }) => (
    <div
      data-testid="sign-in-form"
      data-transferable={String(transferable)}
      data-with-sign-up={String(withSignUp)}
      data-sign-up-redirect={signUpForceRedirectUrl}
    />
  ),
  SignUp: ({
    forceRedirectUrl,
    signInForceRedirectUrl,
  }: {
    forceRedirectUrl?: string
    signInForceRedirectUrl?: string
  }) => (
    <div
      data-testid="register-form"
      data-sign-up-redirect={forceRedirectUrl}
      data-sign-in-redirect={signInForceRedirectUrl}
    />
  ),
  useAuth: () => ({ isLoaded: true, isSignedIn: false }),
  useSignIn: () => ({
    errors: {
      fields: {
        identifier: clerkMock.identifierError,
        password: clerkMock.passwordError,
        code: null,
      },
      global:
        clerkMock.globalErrorCodes.length > 0
          ? [
              {
                isClerkAPIResponseError: () => true,
                errors: clerkMock.globalErrorCodes.map((code) => ({ code })),
              },
            ]
          : null,
      raw: null,
    },
  }),
}))

/** Renders the login and registration pages under the requested auth URL. */
function renderAuthRoute(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login/*" element={<LoginPage />} />
        <Route path="/register/*" element={<RegisterPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    clerkMock.identifierError = null
    clerkMock.passwordError = null
    clerkMock.globalErrorCodes = []
  })

  it('shows the register-first message on login for an unknown email account', async () => {
    clerkMock.identifierError = {
      code: 'form_identifier_not_found',
      message: 'Identifier not found',
    }

    renderAuthRoute('/login')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      unknownAccountMessage,
    )
    expect(screen.getByTestId('sign-in-form')).toBeInTheDocument()
    expect(screen.queryByTestId('register-form')).not.toBeInTheDocument()
  })

  it('allows Google sign-up transfer without showing the email account message', () => {
    clerkMock.globalErrorCodes = ['external_account_not_found']

    renderAuthRoute('/login/sso-callback')

    expect(screen.getByTestId('sign-in-form')).toHaveAttribute(
      'data-transferable',
      'true',
    )
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByTestId('register-form')).not.toBeInTheDocument()
  })

  it('does not redirect users when their existing account has an incorrect password', () => {
    clerkMock.passwordError = {
      code: 'form_password_incorrect',
      message: 'Incorrect password',
    }

    renderAuthRoute('/login')

    expect(screen.getByTestId('sign-in-form')).toBeInTheDocument()
    expect(screen.queryByTestId('register-form')).not.toBeInTheDocument()
  })

  it('routes successful Google sign-ups home and matches nested callback routes', () => {
    renderAuthRoute('/login/sso-callback')

    expect(screen.getByTestId('sign-in-form')).toHaveAttribute(
      'data-with-sign-up',
      'false',
    )
    expect(screen.getByTestId('sign-in-form')).toHaveAttribute(
      'data-sign-up-redirect',
      '/',
    )
  })

  it('keeps the existing email registration completion flow and sends linked sign-ins home', () => {
    renderAuthRoute('/register')

    expect(screen.getByTestId('register-form')).toHaveAttribute(
      'data-sign-up-redirect',
      '/registration-complete',
    )
    expect(screen.getByTestId('register-form')).toHaveAttribute(
      'data-sign-in-redirect',
      '/',
    )
  })
})
