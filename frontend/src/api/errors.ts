export class ApiError extends Error {
  readonly status: number
  readonly code: string

  /** Creates an API error with the server status and stable error code. */
  constructor(
    message: string,
    status: number,
    code: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/** Identifies non-null objects before inspecting error-envelope fields. */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

/** Converts the backend error envelope into a typed client error. */
export function createApiError(status: number, payload: unknown): ApiError {
  const error = isRecord(payload) && isRecord(payload.error) ? payload.error : null
  const code = error && typeof error.code === 'string' ? error.code : 'http_error'
  const message =
    error && typeof error.message === 'string'
      ? error.message
      : `The request failed with status ${status}.`

  return new ApiError(message, status, code)
}
