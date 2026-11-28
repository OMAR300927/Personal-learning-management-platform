import { Outlet } from 'react-router-dom'

/** Provides the branded, responsive frame shared by authentication pages. */
export function AuthLayout() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#101613] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-5 py-5 sm:px-8 lg:px-12">
        <header className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-10 place-items-center rounded-full bg-emerald-300 font-bold text-emerald-950"
          >
            PL
          </span>
          <span className="text-sm font-semibold tracking-wide">
            Personal Learning
          </span>
        </header>

        <div className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[minmax(0,1fr)_minmax(380px,0.78fr)] lg:gap-16">
          <section className="relative hidden min-h-[560px] flex-col justify-between overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#1c2a23] via-[#17211d] to-[#101613] p-10 lg:flex xl:p-14">
            <div
              aria-hidden="true"
              className="absolute -right-20 -top-20 size-96 rounded-full bg-emerald-300/10 blur-3xl"
            />
            <div className="relative max-w-xl">
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">
                Make room to grow
              </p>
              <h1 className="mt-6 text-5xl font-semibold leading-tight tracking-tight text-white xl:text-6xl">
                Build a learning habit that lasts.
              </h1>
              <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
                Keep your paths, learning time, and weekly goals in one calm
                place.
              </p>
            </div>

            <div className="relative grid grid-cols-2 gap-4">
              <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5 backdrop-blur">
                <p className="text-sm text-slate-400">Your focus</p>
                <p className="mt-2 text-xl font-medium text-white">
                  One step at a time
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5 backdrop-blur">
                <p className="text-sm text-slate-400">Your progress</p>
                <p className="mt-2 text-xl font-medium text-emerald-300">
                  Made visible
                </p>
              </div>
            </div>
          </section>

          <section className="mx-auto w-full max-w-md rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur sm:p-9">
            <Outlet />
          </section>
        </div>

        <footer className="py-2 text-center text-xs text-slate-500">
          Your personal space for learning and progress
        </footer>
      </div>
    </main>
  )
}
