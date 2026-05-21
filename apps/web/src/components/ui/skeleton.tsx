import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-[#2a2a2a]',
        className
      )}
    />
  )
}

export function WorkflowCardSkeleton() {
  return (
    <div className="rounded-xl border border-[#2a2a2a] bg-[#1c1c1c] p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 4 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-[#2a2a2a]">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" style={{ opacity: 1 - i * 0.15 }} />
      ))}
    </div>
  )
}

export function PageSkeleton({ rows = 6, type = 'list' }: { rows?: number; type?: 'list' | 'cards' }) {
  if (type === 'cards') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        {Array.from({ length: rows }).map((_, i) => (
          <WorkflowCardSkeleton key={i} />
        ))}
      </div>
    )
  }
  return (
    <div className="flex flex-col">
      {Array.from({ length: rows }).map((_, i) => (
        <TableRowSkeleton key={i} />
      ))}
    </div>
  )
}
