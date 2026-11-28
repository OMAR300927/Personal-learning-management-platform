import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider as ClerkSdkProvider } from '@clerk/react'
import type { PropsWithChildren } from 'react'
import { BrowserRouter } from 'react-router-dom'

const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

/** Configures query caching, Clerk authentication, and browser navigation. */
export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      {clerkPublishableKey ? (
        <ClerkSdkProvider publishableKey={clerkPublishableKey}>
          <BrowserRouter>{children}</BrowserRouter>
        </ClerkSdkProvider>
      ) : (
        <div
          role="alert"
          className="m-6 rounded-xl border border-amber-400/30 bg-slate-950 p-5 text-amber-100"
        >
          Authentication is not configured. Set VITE_CLERK_PUBLISHABLE_KEY in
          frontend/.env and restart the development server.
        </div>
      )}
    </QueryClientProvider>
  )
}
