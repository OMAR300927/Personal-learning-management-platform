export const SESSION_EXPIRED_EVENT = 'personal-learning:session-expired'

const authenticatedSessionKey = 'personal-learning:authenticated-session'
const unsavedFormKeyPrefix = 'personal-learning:unsaved-form:'

/** Records that this tab has had an authenticated session. */
export function markAuthenticatedSession() {
  window.sessionStorage.setItem(authenticatedSessionKey, 'true')
}

/** Reports whether this tab previously held an authenticated session. */
export function hasAuthenticatedSession() {
  return window.sessionStorage.getItem(authenticatedSessionKey) === 'true'
}

/** Removes the tab's authenticated-session marker. */
export function clearAuthenticatedSession() {
  window.sessionStorage.removeItem(authenticatedSessionKey)
}

/** Notifies the app that an API request was rejected as unauthenticated. */
export function notifySessionExpired() {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
}

/** Namespaced storage key for a form draft that survives route changes. */
export function getUnsavedFormKey(formId: string) {
  return `${unsavedFormKeyPrefix}${formId}`
}
