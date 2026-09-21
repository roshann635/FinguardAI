import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  ArrowLeftRight,
  PieChart,
  ShieldAlert,
  LineChart,
  Brain,
  CheckCircle,
  FileText,
  BookOpen,
  Settings,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/performance', label: 'Financial Performance', icon: TrendingUp },
  { to: '/cashflow', label: 'Cash Flow', icon: ArrowLeftRight },
  { to: '/budget', label: 'Budget & Expenses', icon: PieChart },
  { to: '/risk', label: 'Risk Intelligence', icon: ShieldAlert },
  { to: '/forecasts', label: 'Forecasts', icon: LineChart },
  { to: '/ai-analyst', label: 'AI Analyst', icon: Brain },
  { to: '/data-quality', label: 'Data Quality', icon: CheckCircle },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/methodology', label: 'Methodology & Ethics', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
]


export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-slate-900 flex flex-col z-20">
      {/* Logo */}
      <div className="px-5 pt-6 pb-5 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 bg-primary-600 rounded-md flex items-center justify-center">
            <ShieldAlert size={18} className="text-white" />
          </div>
          <span className="text-white font-bold text-lg leading-tight">FinGuard AI</span>
        </div>
        <p className="text-slate-400 text-xs leading-snug ml-10">
          AI Financial Intelligence Platform
        </p>
        <span className="mt-2 inline-block bg-orange-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded uppercase tracking-wide">
          Demo Dataset
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors mb-0.5',
                isActive
                  ? 'bg-primary-700 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              )
            }
          >
            <Icon size={16} className="flex-shrink-0" />
            <span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-slate-700">
        <p className="text-slate-500 text-[11px]">FinGuard AI v1.0.0</p>
        <p className="text-slate-600 text-[11px]">Powered by Google Gemini</p>
      </div>
    </aside>
  )
}
