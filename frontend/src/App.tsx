import type { ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Overview from './pages/Overview'
import FinancialPerformance from './pages/FinancialPerformance'
import RiskIntelligence from './pages/RiskIntelligence'
import Forecasts from './pages/Forecasts'
import AIAnalyst from './pages/AIAnalyst'
import DataQuality from './pages/DataQuality'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import Methodology from './pages/Methodology'

const PAGE_TITLES: Record<string, string> = {
  '/overview': 'Executive Overview',
  '/performance': 'Financial Performance',
  '/cashflow': 'Cash Flow Analysis',
  '/budget': 'Budget & Expense Variances',
  '/risk': 'Risk Intelligence',
  '/forecasts': 'Revenue Forecasts',
  '/ai-analyst': 'AI Analyst',
  '/data-quality': 'Data Quality',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/methodology': 'Analytics Methodology & Governance',
}

function LayoutRoute({ path, element }: { path: string; element: ReactNode }) {
  return <Layout title={PAGE_TITLES[path] ?? 'FinGuard AI'}>{element}</Layout>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<LayoutRoute path="/overview" element={<Overview />} />} />
        <Route path="/performance" element={<LayoutRoute path="/performance" element={<FinancialPerformance defaultTab="revenue" />} />} />
        <Route path="/cashflow" element={<LayoutRoute path="/cashflow" element={<FinancialPerformance defaultTab="cashflow" />} />} />
        <Route path="/budget" element={<LayoutRoute path="/budget" element={<FinancialPerformance defaultTab="budget" />} />} />
        <Route path="/risk" element={<LayoutRoute path="/risk" element={<RiskIntelligence />} />} />
        <Route path="/forecasts" element={<LayoutRoute path="/forecasts" element={<Forecasts />} />} />
        <Route path="/ai-analyst" element={<LayoutRoute path="/ai-analyst" element={<AIAnalyst />} />} />
        <Route path="/data-quality" element={<LayoutRoute path="/data-quality" element={<DataQuality />} />} />
        <Route path="/reports" element={<LayoutRoute path="/reports" element={<Reports />} />} />
        <Route path="/methodology" element={<LayoutRoute path="/methodology" element={<Methodology />} />} />
        <Route path="/settings" element={<LayoutRoute path="/settings" element={<Settings />} />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

