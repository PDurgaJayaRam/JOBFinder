import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import JobSearch from './components/JobSearch'
import LeadGen from './components/LeadGen'
import ComboRun from './components/ComboRun'
import Analytics from './components/Analytics'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<JobSearch />} />
          <Route path="/leads" element={<LeadGen />} />
          <Route path="/combo" element={<ComboRun />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
