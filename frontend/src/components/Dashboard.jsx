import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Briefcase, Users, Mail, Activity } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    axios.get(`${API}/analytics/dashboard`).then((r) => setStats(r.data))
  }, [])

  const cards = [
    { label: 'Applications', value: stats?.total_applications ?? 0, icon: Briefcase, color: 'bg-blue-100 text-blue-700' },
    { label: 'Outreach', value: stats?.total_outreach ?? 0, icon: Mail, color: 'bg-green-100 text-green-700' },
    { label: 'Status Types', value: stats ? Object.keys(stats.status_breakdown).length : 0, icon: Activity, color: 'bg-purple-100 text-purple-700' },
    { label: 'Active Jobs', value: 0, icon: Users, color: 'bg-orange-100 text-orange-700' },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-500 mb-8">Overview of your autonomous AI agent activity.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${c.color}`}>
                <c.icon size={22} />
              </div>
            </div>
            <div className="text-2xl font-bold">{c.value}</div>
            <div className="text-sm text-gray-500">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold mb-4">Status Breakdown</h2>
        {stats?.status_breakdown ? (
          <div className="space-y-3">
            {Object.entries(stats.status_breakdown).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="capitalize font-medium">{status}</span>
                <span className="bg-gray-100 px-3 py-1 rounded-full text-sm">{count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400">No data yet. Run a pipeline to see analytics.</p>
        )}
      </div>
    </div>
  )
}
