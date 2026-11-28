import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { useSessionFormState } from './useSessionFormState'

describe('useSessionFormState', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('restores an unsaved draft after the form is remounted', () => {
    const { result, unmount } = renderHook(() =>
      useSessionFormState('task-edit:task-1', { title: '' }),
    )

    act(() => {
      result.current.setValue({ title: 'Review session recovery' })
    })
    unmount()

    const restored = renderHook(() =>
      useSessionFormState('task-edit:task-1', { title: '' }),
    )

    expect(restored.result.current.value).toEqual({
      title: 'Review session recovery',
    })

    act(() => {
      restored.result.current.clearValue()
    })
    expect(restored.result.current.value).toEqual({ title: '' })
  })
})
