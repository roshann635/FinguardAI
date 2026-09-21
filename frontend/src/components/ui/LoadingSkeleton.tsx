import clsx from 'clsx'

interface LoadingSkeletonProps {
  height?: string
  width?: string
  className?: string
}

export default function LoadingSkeleton({ height = 'h-4', width = 'w-full', className }: LoadingSkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-slate-200 rounded',
        height,
        width,
        className
      )}
    />
  )
}
