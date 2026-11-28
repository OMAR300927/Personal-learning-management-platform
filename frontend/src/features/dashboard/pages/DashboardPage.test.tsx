import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderWithProviders } from '../../../test/test-utils'
import { DashboardPage } from './DashboardPage'

describe('DashboardPage', () => {
  it('renders the dashboard heading and links to the learning features', () => {
    renderWithProviders(<DashboardPage />)

    expect(
      screen.getByRole('heading', { name: 'Dashboard' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', {
        name: 'Consistent progress starts with one focused session.',
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Explore learning paths/ }),
    ).toHaveAttribute('href', '/learning-paths')
    expect(
      screen.getByRole('link', { name: /Log a learning session/ }),
    ).toHaveAttribute('href', '/learning-time')
  })
})
