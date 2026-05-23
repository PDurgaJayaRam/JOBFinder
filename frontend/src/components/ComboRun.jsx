import React, { useState } from 'react'
import axios from 'axios'
import { Zap, Loader2, CheckCircle } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ComboRun() {
  const [resume, setResume] = useState('Python developer with SQL and API experience. B.Tech CS fresher.')
  const [keywords, setKeywords] = useState('Python, Data Analyst')
  const [locations, setLocations] = useState('Hyderabad')
  const [autoApply, setAutoApply] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const run = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API}/combo/run`, {
        resume_text: resume,
        keywords: keywords.split(',').map((s) => s.trim()),
        locations: locations.split(',').map((s) => s.trim()),
        auto_apply: autoApply,
        match_threshold: 75,
      })
      setResult(r.data)
    } catch (e) {
      setResult({ success: false, detail: e.response?.data?.detail || e.message })
    }
    setLoading(false)
  }

  const job = result?.job_pipeline || {}
  const lead = result?.lead_pipeline || {}

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Combo Run</h1>
      <p className="text-gray-500 mb-6">Run both the job search pipeline and lead generation pipeline in parallel.</p>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Resume Summary</label>
          <textarea
            className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            value={resume}
            onChange={(e) => setResume(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Keywords</label>
            <input
              className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Locations</label>
            <input
              className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={locations}
              onChange={(e) => setLocations(e.target.value)}
            />
          </div>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={autoApply} onChange={(e) => setAutoApply(e.target.checked)} />
          <span className="text-sm font-medium">Enable Auto-Apply</span>
        </label>
        <button
          onClick={run}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-5 py-2.5 rounded-lg font-medium transition disabled:opacity-60"
        >
          {loading ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
          {loading ? 'Running Combo Pipeline...' : 'Run Combo Pipeline'}
        </button>
      </div>

      {result && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold mb-3">Job Pipeline</h3>
            {result.success ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-green-700"><CheckCircle size={16} /> Completed</div>
                <div>Discovered: <strong>{job.jobs_discovered}</strong></div>
                <div>Matched: <strong>{job.jobs_matched}</strong></div>
                <div>Applied: <strong>{job.applications_submitted}</strong></div>
              </div>
            ) : (
              <div className="text-red-600 text-sm">{result.detail}</div>
            )}
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold mb-3">Lead Pipeline</h3>
            {result.success ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-green-700"><CheckCircle size={16} /> Completed</div>
                <div>Leads: <strong>{lead.leads_generated}</strong></div>
                <div>Messages: <strong>{lead.messages_generated}</strong></div>
              </div>
            ) : (
              <div className="text-red-600 text-sm">{result.detail}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
