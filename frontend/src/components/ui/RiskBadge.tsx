import type { RiskLevel } from '../../types'
import clsx from 'clsx'

interface RiskBadgeProps {
  level: RiskLevel
}

const STYLES: Record<RiskLevel, string> = {
  LOW: 'bg-green-100 text-green-800 border border-green-300',
  MEDIUM: 'bg-amber-100 text-amber-800 border border-amber-300',
  HIGH: 'bg-red-100 text-red-800 border border-red-300',
  CRITICAL: 'bg-red-900 text-red-100 border border-red-800',
}

export default function RiskBadge({ level }: RiskBadgeProps) {
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide', STYLES[level])}>
      {level}
    </span>
  )
}
