import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'
import { badgeVariants, type BadgeVariantProps } from './badge.variants'

const dotColors: Record<string, string> = {
  default: 'bg-text-dim',
  ok:      'bg-ok shadow-[0_0_5px_var(--ok)]',
  warn:    'bg-warn',
  err:     'bg-err shadow-[0_0_5px_var(--err)]',
  accent:  'bg-accent',
  draft:   'bg-text-dim',
  secondary: 'bg-text-dim',
  destructive: 'bg-err shadow-[0_0_5px_var(--err)]',
  outline: 'bg-text-dim',
}

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    BadgeVariantProps {
  dot?: boolean
}

/**
 * RunMyCrew Badge — CVA-based status / label chips.
 * Supports legacy `dot` status indicator and custom variants.
 */
function Badge({ className, variant = 'default', dot, children, ...props }: BadgeProps) {
  const activeVariant = variant || 'default'
  return (
    <div className={cn(badgeVariants({ variant: activeVariant }), className)} {...props}>
      {dot && <span className={cn('w-1 h-1 rounded-full shrink-0 mr-0.5', dotColors[activeVariant])} />}
      {children}
    </div>
  )
}

export { Badge }
