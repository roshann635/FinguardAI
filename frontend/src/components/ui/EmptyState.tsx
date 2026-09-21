import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  message: string
  icon?: ReactNode
}

export default function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
      <span className="text-slate-300">
        {icon ?? <Inbox size={36} />}
      </span>
      <p className="text-sm text-slate-500 max-w-xs">{message}</p>
    </div>
  )
}
