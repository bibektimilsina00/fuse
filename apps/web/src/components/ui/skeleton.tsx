import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

/**
 * RunMyCrew Skeleton — shimmer placeholder for loading states.
 */
function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-[6px] bg-surface-2',
        className,
      )}
      {...props}
    />
  )
}

/**
 * Multi-line text skeleton with configurable lines.
 */
function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={cn('h-3', i === lines - 1 && lines > 1 ? 'w-3/5' : 'w-full')}
        />
      ))}
    </div>
  )
}

/**
 * Card-shaped skeleton.
 */
function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-[10px] border border-border-faint p-4 space-y-3', className)}>
      <Skeleton className="h-4 w-1/3" />
      <SkeletonText lines={2} />
    </div>
  )
}

export { Skeleton, SkeletonText, SkeletonCard }
