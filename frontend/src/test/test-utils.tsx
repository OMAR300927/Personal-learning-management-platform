import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { PropsWithChildren, ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'

/** Creates an isolated query cache for each component test. */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
}

/** Supplies router and query context to test-rendered components. */
export function TestProviders({
  children,
}: PropsWithChildren<{ initialEntries?: string[] }>) {
  return (
    <QueryClientProvider client={createTestQueryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

/** Renders a component with the shared test providers. */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  return render(ui, {
    ...options,
    wrapper: TestProviders,
  })
}
