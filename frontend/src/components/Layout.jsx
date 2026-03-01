import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { FEATURES } from '../config/features'

const navLinkClass = ({ isActive }) =>
  `flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    isActive ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'
  }`

export default function Layout() {
  const { user, logout } = useAuth()
  const { addToast }     = useToast()
  const navigate         = useNavigate()
  const [open, setOpen]  = useState(false)

  const handleLogout = async () => {
    await logout()
    addToast('Logged out successfully', 'info')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Top nav ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex h-14 items-center justify-between px-4">

          {/* Hamburger (mobile) + logo */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="Open navigation menu"
              aria-expanded={open}
              aria-controls="sidebar"
              className="md:hidden rounded p-1 text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => setOpen(true)}
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <Link
              to="/"
              className="text-lg font-bold text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            >
              🏦 BankApp
            </Link>
          </div>

          {/* User + logout */}
          <div className="flex items-center gap-3">
            <span className="hidden sm:block text-sm text-gray-600 truncate max-w-[160px]">
              {user?.full_name}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Mobile overlay */}
        {open && (
          <div
            className="fixed inset-0 z-20 bg-black/40 md:hidden"
            aria-hidden="true"
            onClick={() => setOpen(false)}
          />
        )}

        {/* ── Sidebar ────────────────────────────────────────────────────── */}
        <nav
          id="sidebar"
          aria-label="Main navigation"
          className={`
            fixed z-30 inset-y-0 left-0 w-56 bg-white border-r border-gray-200 pt-14
            transform transition-transform
            md:translate-x-0 md:static md:z-auto md:h-auto md:pt-0
            ${open ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <button
            type="button"
            aria-label="Close navigation menu"
            className="absolute top-3 right-3 md:hidden text-gray-500 hover:text-gray-700 text-xl leading-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            onClick={() => setOpen(false)}
          >
            ×
          </button>

          <ul className="p-3 space-y-1" role="list">
            <li>
              <NavLink to="/" end className={navLinkClass} onClick={() => setOpen(false)}>
                📋 Dashboard
              </NavLink>
            </li>
            {FEATURES.TRANSFERS && (
              <li>
                <NavLink to="/transfer" className={navLinkClass} onClick={() => setOpen(false)}>
                  💸 New Transfer
                </NavLink>
              </li>
            )}
          </ul>
        </nav>

        {/* ── Page content ─────────────────────────────────────────────── */}
        <main
          id="main-content"
          className="flex-1 p-4 md:p-6 min-h-[calc(100vh-3.5rem)]"
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
