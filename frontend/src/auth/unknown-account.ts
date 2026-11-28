import type { useSignIn } from '@clerk/react'

type SignInErrors = ReturnType<typeof useSignIn>['errors']

const unknownEmailErrorCodes = new Set(['form_identifier_not_found'])

export const unknownAccountMessage =
  "You don't have an account, please register first."

/** Detects Clerk errors indicating that the submitted email has no account. */
export function isUnknownEmailError(errors: SignInErrors): boolean {
  if (
    errors.fields.identifier &&
    unknownEmailErrorCodes.has(errors.fields.identifier.code)
  ) {
    return true
  }

  return (
    errors.global?.some(
      (error) =>
        error.isClerkAPIResponseError() &&
        error.errors.some(({ code }) => unknownEmailErrorCodes.has(code)),
    ) ?? false
  )
}
