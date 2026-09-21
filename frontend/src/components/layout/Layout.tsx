import { useState, createContext, useContext, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export interface FilterContextValue {
  period: string
  region: string
}

export const FilterContext = createContext<FilterContextValue>({
  period: 'last_12_months',
  region: 'all',
})

export const useFilters = () => useContext(FilterContext)

interface LayoutProps {
  title: string
  children: ReactNode
}

export default function Layout({ title, children }: LayoutProps) {
  const [period, setPeriod] = useState('last_12_months')
  const [region, setRegion] = useState('all')

  return (
    <FilterContext.Provider value={{ period, region }}>
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 ml-60">
          <TopBar
            title={title}
            period={period}
            region={region}
            onPeriodChange={setPeriod}
            onRegionChange={setRegion}
          />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </FilterContext.Provider>
  )
}
