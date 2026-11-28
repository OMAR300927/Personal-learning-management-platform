import { AppProviders } from './providers'
import { AppRouter } from './router'

/** Renders the app router inside the shared provider tree. */
export default function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  )
}
