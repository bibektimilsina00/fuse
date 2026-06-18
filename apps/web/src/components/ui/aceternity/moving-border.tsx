'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/cn'

interface MovingBorderProps {
  children: React.ReactNode
  className?: string
  containerClassName?: string
  /** Animation duration in seconds. */
  duration?: number
  /** Border color — defaults to accent. */
  borderColor?: string
  borderWidth?: number
  borderRadius?: string
}

/**
 * MovingBorder — animated gradient border that travels around the element perimeter.
 * Adapted from Aceternity UI for Fuse. Uses framer-motion for the conic-gradient animation.
 * @example
 * ```tsx
 * <MovingBorder>
 *   <Button variant="secondary">New Workflow</Button>
 * </MovingBorder>
 * ```
 */
function MovingBorder({
  children,
  className,
  containerClassName,
  duration = 3,
  borderColor,
  borderWidth = 1.5,
  borderRadius = '10px',
}: MovingBorderProps) {
  const color = borderColor ?? 'var(--accent)'

  return (
    <div
      className={cn('relative inline-flex p-[1.5px] overflow-hidden', containerClassName)}
      style={{ borderRadius }}
    >
      {/* Animated conic-gradient border */}
      <motion.div
        className="absolute inset-0"
        style={{ borderRadius: `calc(${borderRadius} + ${borderWidth}px)` }}
        animate={{ rotate: 360 }}
        transition={{ duration, repeat: Infinity, ease: 'linear' }}
      >
        <div
          className="absolute inset-[-100%]"
          style={{
            background: `conic-gradient(from 0deg, transparent 0deg, ${color} 90deg, transparent 180deg)`,
          }}
        />
      </motion.div>

      {/* Content */}
      <div
        className={cn('relative z-10', className)}
        style={{ borderRadius: `calc(${borderRadius} - ${borderWidth}px)` }}
      >
        {children}
      </div>
    </div>
  )
}

export { MovingBorder }
