import React, { useState } from 'react'
import axios from 'axios'
import { Users, Loader2, CheckCircle } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function LeadGen() {
  const [companyJson, setCompanyJson] = useState(
    JSON.stringify([
      { company_name: "Example BV", website: "https://example.com", raw_data: { snippet: "We are a growing accounting firm using Excel and manual processes." } }
    ], null, 2)
  )
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const run = async () => {
    setLoading(true)
    try {
      const companies = JSON.parse(companyJson)
      const r = await axios.post(`${API}/leads/enrich`, { companies })
      setResult(r.data)
    } catch (e) {
      setResult({ success: false, detail: e.response?.data?.detail || e.message })
    }
    setLoading(false)
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Lead Generation</h1>
      <p className="text-gray-500 mb-6">Analyze companies, detect pain signals, and generate outreach.</p>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Company JSON</label>
          <textarea
            className="w-full border rounded-lg p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={10}
            value={companyJson}
            onChange={(e) => setCompanyJson(e.target.value)}
          />
          <p className="text-xs text-gray-400 mt-1">Paste an array of company objects. The AI will enrich each one.</p>
        </div>

        <button
          onClick={run}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-5 py-2.5 rounded-lg font-medium transition disabled:opacity-60"
        >
          {loading ? <Loader2 className="animate-spin" size={18} /> : <Users size={18} />}
          {loading ? 'Enriching...' : 'Enrich Leads'}
        </button>
      </div>

      {result && (
        <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold mb-3">Result</h3>
          {result.success ? (
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-green-700"><CheckCircle size={16} /> Enrichment completed</div>
              <div>Leads Generated: <strong>{result.leads_generated}</strong></div>
              <div>Messages Generated: <strong>{result.messages_generated}</strong></div>
            </div>
          ) : (
            <div className="text-red-600 text-sm">{result.detail}</div>
          )}
        </div>
      )}
    </div>
  )
}
