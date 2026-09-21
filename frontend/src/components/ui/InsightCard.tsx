import type { InsightCard as InsightCardType } from '../../types'
import clsx from 'clsx'

const TYPE_STYLES = {
  FACT: {
    bg: 'bg-blue-50',
    border: 'border-l-4 border-blue-600',
    badge: 'bg-blue-100 text-blue-700',
    label: 'FACT',
  },
  INSIGHT: {
    bg: 'bg-purple-50',
    border: 'border-l-4 border-purple-600',
    badge: 'bg-purple-100 text-purple-700',
    label: 'INSIGHT',
  },
  RISK: {
    bg: 'bg-red-50',
    border: 'border-l-4 border-red-600',
    badge: 'bg-red-100 text-red-700',
    label: 'RISK',
  },
  OPPORTUNITY: {
    bg: 'bg-green-50',
    border: 'border-l-4 border-green-600',
    badge: 'bg-green-100 text-green-700',
    label: 'OPPORTUNITY',
  },
  ACTION: {
    bg: 'bg-orange-50',
    border: 'border-l-4 border-orange-600',
    badge: 'bg-orange-100 text-orange-700',
    label: 'ACTION',
  },
}

interface InsightCardProps {
  card: InsightCardType
}

export default function InsightCardComponent({ card }: InsightCardProps) {
  const styles = TYPE_STYLES[card.type]
  return (
    <div className={clsx('rounded-lg p-4', styles.bg, styles.border)}>
      <div className="flex items-start gap-2 mb-2">
        <span className={clsx('text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide', styles.badge)}>
          {styles.label}
          {card.type === 'RISK' && card.severity && ` · ${card.severity}`}
        </span>
        {card.priority && card.type === 'ACTION' && (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase bg-orange-200 text-orange-800">
            {card.priority}
          </span>
        )}
      </div>
      <h4 className="text-sm font-semibold text-slate-800 mb-1">{card.title}</h4>
      <p className="text-sm text-slate-700 leading-snug">{card.body}</p>
      {card.evidence && (
        <p className="mt-2 text-xs text-slate-500 italic">{card.evidence}</p>
      )}
      {card.metric_source && (
        <p className="mt-1 text-[11px] text-slate-400">Source: {card.metric_source}</p>
      )}
    </div>
  )
}
