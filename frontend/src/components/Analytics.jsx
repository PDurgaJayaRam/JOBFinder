import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const COLORS = ['#3b82f6', '#22c55e', '#a855f7', '#f97316', '#ef4444']

export default function Analytics() {
  const [data, setData] = useState(null)

  useEffect(() => {
    axios.get(`${API}/analytics/dashboard`).then((r) => setData(r.data))
  }, [])

  const statusEntries = data?.status_breakdown ? Object.entries(data.status_breakdown).map(([name, value]) => ({ name, value })) : []

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Analytics</h1>
      <p className="text-gray-500 mb-8">Track applications, outreach, and pipeline performance.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Application Status Breakdown</h2>
          {statusEntries.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={statusEntries}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400">No application data yet.</p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Distribution</h2>
          {statusEntries.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={statusEntries} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100}>
                  {statusEntries.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400">No data to display.</p>
          )}
        </div>
      </div>
    </div>
  )
}
