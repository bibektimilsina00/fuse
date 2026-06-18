'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/cn'

interface AuroraBackgroundProps {
  children?: React.ReactNode
  className?: string
  /** Extra intensity multiplier for the aurora effect (0–2). */
  intensity?: number
}

/**
 * AuroraBackground — animated aurora borealis effect using CSS gradients + framer-motion.
 * Great for auth/onboarding pages. Adapted from Aceternity UI with Fuse accent palette.
 */
function AuroraBackground({ children, className, intensity = 1 }: AuroraBackgroundProps) {
  const opacity = Math.min(intensity * 0.07, 0.14)

  return (
    <div className={cn('relative flex flex-col overflow-hidden', className)}>
      {/* Aurora layer 1 */}
      <motion.div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        animate={{
          backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
        style={{
          backgroundSize: '400% 400%',
          backgroundImage: `
            radial-gradient(ellipse 80% 60% at 20% 40%, var(--accent) ${opacity * 100}%, transparent 70%),
            radial-gradient(ellipse 60% 50% at 80% 60%, var(--ok) ${opacity * 60}%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 50% 20%, var(--accent-soft) 40%, transparent 60%)
          `,
          filter: 'blur(60px)',
        }}
      />

      {/* Aurora layer 2 — offset */}
      <motion.div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        animate={{
          backgroundPosition: ['100% 0%', '0% 100%', '100% 0%'],
        }}
        transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
        style={{
          backgroundSize: '400% 400%',
          backgroundImage: `
            radial-gradient(ellipse 70% 50% at 70% 30%, var(--accent) ${opacity * 60}%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 30% 70%, oklch(0.55 0.15 280) ${opacity * 50}%, transparent 70%)
          `,
          filter: 'blur(80px)',
          mixBlendMode: 'screen',
        }}
      />

      {children}
    </div>
  )
}

export { AuroraBackground }
