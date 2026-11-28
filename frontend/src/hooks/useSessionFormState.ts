import { useCallback, useState } from 'react'
import { getUnsavedFormKey } from '../auth/session-expiry'

/** Restores a saved form draft, or returns the supplied initial value. */
function readFormState<T>(storageKey: string, initialValue: T): T {
  const storedValue = window.sessionStorage.getItem(storageKey)
  return storedValue === null ? initialValue : (JSON.parse(storedValue) as T)
}

/** Keeps form values in session storage so drafts survive a login redirect. */
export function useSessionFormState<T>(formId: string, initialValue: T) {
  const storageKey = getUnsavedFormKey(formId)
  const [value, setValue] = useState(() => {
    // Load the draft lazily so storage is read only when the form mounts.
    return readFormState(storageKey, initialValue)
  })

  /** Persists the latest draft before updating the rendered form state. */
  const updateValue = useCallback(
    (nextValue: T) => {
      window.sessionStorage.setItem(storageKey, JSON.stringify(nextValue))
      setValue(nextValue)
    },
    [storageKey],
  )

  /** Removes the saved draft and restores the form's initial value. */
  const clearValue = useCallback(() => {
    window.sessionStorage.removeItem(storageKey)
    setValue(initialValue)
  }, [initialValue, storageKey])

  return { value, setValue: updateValue, clearValue }
}
