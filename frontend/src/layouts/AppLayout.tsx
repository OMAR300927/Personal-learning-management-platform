import { NavLink, Outlet } from 'react-router-dom'

const navigation = [
  { to: '/', label: 'Dashboard' },
  { to: '/learning-paths', label: 'Learning paths' },
  { to: '/learning-time', label: 'Learning time' },
  { to: '/weekly-goals', label: 'Weekly goals' },
]

/** Renders the authenticated app shell and primary feature navigation. */
export function AppLayout() {
  return (
    <div className="min-h-screen bg-[#101211] text-slate-100 md:grid md:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="border-b border-white/10 bg-[#171a18] px-4 py-4 text-slate-100 md:flex md:min-h-screen md:flex-col md:border-b-0 md:border-r md:px-5 md:py-6">
        <div className="flex items-center gap-3">
          <div
            aria-hidden="true"
            className="grid size-10 shrink-0 place-items-center rounded-full bg-lime-300 text-xs font-bold tracking-tight text-[#151713]"
          >
            PL
          </div>
          <div>
            <p className="text-sm font-semibold tracking-wide text-white">
              Personal Learning
            </p>
            <p className="mt-0.5 text-xs text-slate-500">Your workspace</p>
          </div>
        </div>
        <nav
          aria-label="Primary navigation"
          className="mt-5 flex gap-2 overflow-x-auto md:flex-col"
        >
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-lime-300 text-[#151713]'
                    : 'text-slate-400 hover:bg-white/[0.06] hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="mt-auto hidden rounded-2xl border border-white/10 bg-white/[0.035] p-4 text-xs leading-5 text-slate-400 md:block">
          Small, steady steps add up to meaningful progress.
        </p>
      </aside>
      <main className="min-w-0 bg-[#101211] p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}
