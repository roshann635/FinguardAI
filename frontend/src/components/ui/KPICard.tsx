import type { ReactNode } from 'react'
import clsx from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string
  previousValue?: string
  changeAbs?: string
  changePct?: number
  direction?: 'up' | 'down' | 'flat'
  interpretation?: string
  icon?: ReactNode
  colorScheme?: 'default' | 'risk' | 'opportunity'
  onInvestigate?: () => void
}

export default function KPICard({
  title,
  value,
  changeAbs,
  changePct,
  direction = 'flat',
  interpretation,
  icon,
  colorScheme = 'default',
  onInvestigate,
}: KPICardProps) {
  const isUp = direction === 'up'
  const isDown = direction === 'down'

  const changeColor =
    colorScheme === 'risk'
      ? isUp ? 'text-red-600' : isDown ? 'text-green-600' : 'text-slate-500'
      : colorScheme === 'opportunity'
      ? isUp ? 'text-green-600' : isDown ? 'text-red-600' : 'text-slate-500'
      : isUp ? 'text-green-600' : isDown ? 'text-red-600' : 'text-slate-500'

  const ChangeIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 flex flex-col gap-2 min-h-[130px] hover:border-slate-300 transition-colors relative group">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</span>
        <div className="flex items-center gap-1.5">
          {onInvestigate && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onInvestigate()
              }}
              title={`Investigate ${title} root causes`}
              className="text-[11px] font-semibold text-primary-700 hover:text-primary-800 bg-primary-50 hover:bg-primary-100 border border-primary-200 px-1.5 py-0.5 rounded transition-colors flex items-center gap-0.5 shadow-2xs"
            >
              Why?
            </button>
          )}
          {icon && <span className="text-slate-400">{icon}</span>}
        </div>
      </div>

      <div className="text-[2rem] font-bold text-slate-800 leading-none">{value}</div>

      {(changeAbs != null || changePct != null) && (
        <div className={clsx('flex items-center gap-1 text-sm font-medium', changeColor)}>
          <ChangeIcon size={14} />
          <span>
            {changeAbs != null && changeAbs}
            {changePct != null && ` (${changePct > 0 ? '+' : ''}${changePct.toFixed(1)}%)`}
          </span>
        </div>
      )}

      {interpretation && (
        <p className="text-xs text-slate-500 leading-snug mt-auto">{interpretation}</p>
      )}
    </div>
  )
}
