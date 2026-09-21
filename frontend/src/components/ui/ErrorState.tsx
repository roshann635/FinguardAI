import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorStateProps {
  message: string
  retry?: () => void
}

export default function ErrorState({ message, retry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
      <AlertCircle size={32} className="text-red-400" />
      <p className="text-sm text-slate-600 max-w-sm">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-800 font-medium transition-colors"
        >
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  )
}
