import React, { useState } from 'react'
import axios from 'axios'
import { Search, Loader2, CheckCircle, XCircle } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function JobSearch() {
  const [resume, setResume] = useState('Python developer with SQL and API experience. 0 years professional experience. B.Tech in CS.')
  const [keywords, setKeywords] = useState('Python, Data Analyst')
  const [locations, setLocations] = useState('Hyderabad')
  const [autoApply, setAutoApply] = useState(false)
  const [threshold, setThreshold] = useState(75)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const run = async () => {
    setLoading(true)
    try {
      const r = await axios.post(`${API}/jobs/search`, {
        resume_text: resume,
        keywords: keywords.split(',').map((s) => s.trim()),
        locations: locations.split(',').map((s) => s.trim()),
        auto_apply: autoApply,
        match_threshold: threshold,
        max_jobs: 20,
      })
      setResult(r.data)
    } catch (e) {
      setResult({ success: false, detail: e.response?.data?.detail || e.message })
    }
    setLoading(false)
  }

  const exportCSV = async () => {
    try {
      const r = await axios.post(`${API}/jobs/export/csv`, {
        resume_text: resume,
        keywords: keywords.split(',').map((s) => s.trim()),
        locations: locations.split(',').map((s) => s.trim()),
        auto_apply: false,
        match_threshold: 0,
        max_jobs: 20,
      }, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'jobs_export.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (e) {
      alert('Export failed: ' + (e.response?.data?.detail || e.message))
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Job Search + Match</h1>
      <p className="text-gray-500 mb-6">Discover jobs, analyze descriptions, and get ATS match scores.</p>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Resume Summary</label>
          <textarea
            className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            value={resume}
            onChange={(e) => setResume(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Keywords (comma separated)</label>
            <input
              className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Locations (comma separated)</label>
            <input
              className="w-full border rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={locations}
              onChange={(e) => setLocations(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={autoApply} onChange={(e) => setAutoApply(e.target.checked)} />
            <span className="text-sm font-medium">Enable Auto-Apply</span>
          </label>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Match Threshold:</span>
            <input
              type="range" min={0} max={100} value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            />
            <span className="text-sm font-mono">{threshold}%</span>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={run}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition disabled:opacity-60"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
            {loading ? 'Running Pipeline...' : 'Search & Match Jobs'}
          </button>
          {result && result.jobs && result.jobs.length > 0 && (
            <button
              onClick={exportCSV}
              disabled={loading}
              className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-lg font-medium transition disabled:opacity-60"
            >
              Export CSV
            </button>
          )}
        </div>
      </div>

      {result && (
        <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold mb-3">Result</h3>
          {result.success ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-700 text-sm"><CheckCircle size={16} /> Pipeline completed</div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-600">{result.jobs_discovered}</div>
                  <div className="text-gray-500 text-xs">Discovered</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">{result.jobs_matched}</div>
                  <div className="text-gray-500 text-xs">Matched</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-purple-600">{result.applications_submitted}</div>
                  <div className="text-gray-500 text-xs">Applied</div>
                </div>
              </div>
              {result.errors?.length > 0 && (
                <div className="text-orange-600 text-sm">
                  <div className="font-medium mb-1">Warnings:</div>
                  <ul className="list-disc pl-5 space-y-1">
                    {result.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
              {result.jobs && result.jobs.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium mb-3">Job Listings ({result.jobs.length})</h4>
                  <div className="space-y-3">
                    {result.jobs.map((job, i) => (
                      <div key={i} className="border rounded-lg p-4 hover:border-blue-300 transition">
                        <div className="flex justify-between items-start mb-2">
                          <h5 className="font-semibold text-gray-900">{job.title || 'Unknown'}</h5>
                          <span className={`text-xs font-medium px-2 py-1 rounded ${
                            (job.match_score || 0) >= 75 ? 'bg-green-100 text-green-700' :
                            (job.match_score || 0) >= 50 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {(job.match_score || 0).toFixed(0)}% match
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 mb-2">
                          {job.company || 'Unknown'} • {job.location || 'Unknown'}
                        </div>
                        {job.source && (
                          <div className="text-xs text-gray-400 mb-2">Source: {job.source}</div>
                        )}
                        {/* AI Analysis Output */}
                        {job.summary && (
                          <div className="text-sm text-gray-700 mb-2 bg-blue-50 p-2 rounded">
                            <span className="font-medium text-blue-800">AI Summary:</span> {job.summary}
                          </div>
                        )}
                        {/* Weighted Match Score Breakdown */}
                        {(job.required_match_percent !== undefined || job.preferred_match_percent !== undefined) && (
                          <div className="text-xs mb-2 bg-gray-50 p-2 rounded">
                            <span className="font-medium text-gray-700">Match Breakdown:</span>{' '}
                            Required: {job.required_match_percent || 0}% |{' '}
                            Preferred: {job.preferred_match_percent || 0}%
                          </div>
                        )}
                        {/* Required Skills */}
                        {job.required_skills && job.required_skills.length > 0 && (
                          <div className="text-xs mb-2">
                            <span className="font-medium text-gray-700">Required Skills:</span>{' '}
                            {job.required_skills.map((s, idx) => (
                              <span key={idx} className="inline-block bg-red-100 text-red-700 px-2 py-0.5 rounded mr-1 mb-1">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {/* Preferred Skills */}
                        {job.preferred_skills && job.preferred_skills.length > 0 && (
                          <div className="text-xs mb-2">
                            <span className="font-medium text-gray-700">Preferred Skills:</span>{' '}
                            {job.preferred_skills.map((s, idx) => (
                              <span key={idx} className="inline-block bg-green-100 text-green-700 px-2 py-0.5 rounded mr-1 mb-1">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {/* Legacy skills display for backward compatibility */}
                        {job.skills && job.skills.length > 0 && !job.required_skills && (
                          <div className="text-xs mb-2">
                            <span className="font-medium text-gray-700">Skills:</span>{' '}
                            {job.skills.map((s, idx) => (
                              <span key={idx} className="inline-block bg-purple-100 text-purple-700 px-2 py-0.5 rounded mr-1 mb-1">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {job.experience_required && (
                          <div className="text-xs text-gray-600 mb-2">
                            <span className="font-medium">Experience:</span> {job.experience_required}
                          </div>
                        )}
                        {job.salary_range && (
                          <div className="text-xs text-gray-600 mb-2">
                            <span className="font-medium">Salary:</span> {job.salary_range}
                          </div>
                        )}
                        {/* Red Flags */}
                        {job.red_flags && (job.red_flags.workload?.length > 0 || job.red_flags.culture?.length > 0 || job.red_flags.compensation?.length > 0) && (
                          <div className="text-xs mb-2 bg-yellow-50 p-2 rounded">
                            <span className="font-medium text-yellow-800">⚠️ Red Flags:</span>
                            {job.red_flags.workload?.length > 0 && (
                              <div className="text-yellow-700">Workload: {job.red_flags.workload.join(', ')}</div>
                            )}
                            {job.red_flags.culture?.length > 0 && (
                              <div className="text-yellow-700">Culture: {job.red_flags.culture.join(', ')}</div>
                            )}
                            {job.red_flags.compensation?.length > 0 && (
                              <div className="text-yellow-700">Compensation: {job.red_flags.compensation.join(', ')}</div>
                            )}
                          </div>
                        )}
                        {/* Gap Analysis */}
                        {job.gap_analysis && (job.gap_analysis.critical_gaps?.length > 0 || job.gap_analysis.major_gaps?.length > 0) && (
                          <div className="text-xs mb-2">
                            <span className="font-medium text-gray-700">Gap Analysis:</span>
                            {job.gap_analysis.critical_gaps?.length > 0 && (
                              <div className="text-red-600">Critical: {job.gap_analysis.critical_gaps.join(', ')}</div>
                            )}
                            {job.gap_analysis.major_gaps?.length > 0 && (
                              <div className="text-orange-600">Major: {job.gap_analysis.major_gaps.join(', ')}</div>
                            )}
                          </div>
                        )}
                        {/* Missing Skills (legacy) */}
                        {job.missing_skills && job.missing_skills.length > 0 && !job.missing_required_skills && (
                          <div className="text-xs text-orange-600 mb-2">
                            <span className="font-medium">Missing Skills:</span> {job.missing_skills.join(', ')}
                          </div>
                        )}
                        {job.missing_required_skills && job.missing_required_skills.length > 0 && (
                          <div className="text-xs text-red-600 mb-2">
                            <span className="font-medium">Missing Required:</span> {job.missing_required_skills.join(', ')}
                          </div>
                        )}
                        {job.missing_preferred_skills && job.missing_preferred_skills.length > 0 && (
                          <div className="text-xs text-orange-600 mb-2">
                            <span className="font-medium">Missing Preferred:</span> {job.missing_preferred_skills.join(', ')}
                          </div>
                        )}
                        {job.description && !job.summary && (
                          <p className="text-sm text-gray-700 mb-2 line-clamp-3">{job.description}</p>
                        )}
                        {job.url && (
                          <a href={job.url} target="_blank" rel="noopener noreferrer"
                             className="text-sm text-blue-600 hover:underline inline-block">
                            View Job →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-600 text-sm"><XCircle size={16} /> {result.detail}</div>
          )}
        </div>
      )}
    </div>
  )
}
