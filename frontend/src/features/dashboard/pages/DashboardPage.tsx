import { Link } from 'react-router-dom'

const dashboardCards = [
  {
    label: 'Learning paths',
    description: 'Organize your next steps into a path that feels achievable.',
    action: 'Explore paths',
    to: '/learning-paths',
    marker: '01',
  },
  {
    label: 'Learning time',
    description: 'Make focused study sessions part of your weekly rhythm.',
    action: 'Log learning time',
    to: '/learning-time',
    marker: '02',
  },
  {
    label: 'Weekly goals',
    description: 'Choose a clear target and celebrate steady progress.',
    action: 'Set a goal',
    to: '/weekly-goals',
    marker: '03',
  },
  {
    label: 'Task progress',
    description: 'Break a learning path into small, finishable tasks.',
    action: 'View your paths',
    to: '/learning-paths',
    marker: '04',
  },
]

/** Renders the dashboard entry point for the user's learning overview. */
export function DashboardPage() {
  return (
    <section
      aria-labelledby="dashboard-heading"
      className="mx-auto max-w-[1440px] space-y-6"
    >
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-lime-300">
            Your learning space
          </p>
          <h1
            id="dashboard-heading"
            className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl"
          >
            Dashboard
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400 sm:text-base">
            A calm place to plan your next step and keep your learning moving.
          </p>
        </div>
        <Link
          to="/learning-paths"
          className="inline-flex min-h-11 items-center justify-center gap-2 self-start rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold text-[#151713] transition-colors hover:bg-lime-200 sm:self-auto"
        >
          Explore learning paths
          <span aria-hidden="true">→</span>
        </Link>
      </header>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(280px,0.8fr)]">
        <article className="relative isolate overflow-hidden rounded-[28px] border border-white/10 bg-gradient-to-br from-[#252b26] via-[#1c211e] to-[#171a18] p-6 shadow-[0_24px_70px_rgba(0,0,0,0.24)] sm:p-8">
          <div
            aria-hidden="true"
            className="absolute -right-16 -top-24 -z-10 size-72 rounded-full border border-lime-200/10 bg-lime-300/[0.04] shadow-[0_0_90px_rgba(190,242,100,0.08)]"
          />
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">
            Start where you are
          </p>
          <h2 className="mt-4 max-w-2xl text-2xl font-medium leading-tight tracking-tight text-white sm:text-4xl">
            Consistent progress starts with one focused session.
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
            Build a learning path, record your time, and set a weekly goal. Your
            overview will grow with you.
          </p>
          <Link
            to="/learning-time"
            className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-lime-200 transition-colors hover:text-lime-100"
          >
            Log a learning session
            <span aria-hidden="true">→</span>
          </Link>
        </article>

        <article className="flex flex-col justify-between rounded-[28px] border border-white/10 bg-white/[0.045] p-6 shadow-[0_20px_60px_rgba(0,0,0,0.18)] sm:p-7">
          <div>
            <div className="flex items-center justify-between gap-4">
              <p className="text-sm font-medium text-slate-300">This week</p>
              <span className="rounded-full border border-lime-200/15 bg-lime-200/[0.08] px-3 py-1 text-xs font-medium text-lime-200">
                Your pace
              </span>
            </div>
            <h2 className="mt-8 text-2xl font-semibold tracking-tight text-white">
              Make time for what matters.
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              A short, focused session is a good place to begin.
            </p>
          </div>
          <Link
            to="/learning-time"
            className="mt-8 inline-flex min-h-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:border-lime-200/30 hover:bg-lime-200/[0.08]"
          >
            Open learning time
          </Link>
        </article>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {dashboardCards.map((card) => (
          <article
            key={card.label}
            className="group rounded-[24px] border border-white/10 bg-white/[0.035] p-5 transition-colors hover:border-white/15 hover:bg-white/[0.055]"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="grid size-11 place-items-center rounded-2xl border border-lime-200/10 bg-lime-200/[0.08] text-xs font-semibold tracking-wide text-lime-200">
                {card.marker}
              </div>
              <span aria-hidden="true" className="text-lg text-slate-500">
                ↗
              </span>
            </div>
            <h2 className="mt-6 text-lg font-semibold text-white">
              {card.label}
            </h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-slate-400">
              {card.description}
            </p>
            <Link
              to={card.to}
              className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-lime-200 transition-colors group-hover:text-lime-100"
            >
              {card.action}
              <span aria-hidden="true">→</span>
            </Link>
          </article>
        ))}
      </div>
    </section>
  )
}
