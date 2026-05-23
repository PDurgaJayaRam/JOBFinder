import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Search, Users, Zap, BarChart3 } from 'lucide-react'

const nav = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/jobs', icon: Search, label: 'Job Search' },
  { to: '/leads', icon: Users, label: 'Lead Gen' },
  { to: '/combo', icon: Zap, label: 'Combo Run' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function Layout({ children }) {
  const { pathname } = useLocation()
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-6 font-bold text-xl tracking-wide">Combo AI Agent</div>
        <nav className="flex-1 px-4 space-y-2">
          {nav.map((item) => {
            const active = pathname === item.to
            return (
              <Link
                key={item.to}
                to={item.to}
                className={
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition ' +
                  (active ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800')
                }
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>
        <div className="p-6 text-xs text-gray-500">v1.0.0 &copy; Combo AI</div>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  )
}
