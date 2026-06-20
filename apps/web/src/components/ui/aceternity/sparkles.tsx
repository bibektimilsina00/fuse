'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/cn'

interface Particle {
  id: number
  x: number
  y: number
  size: number
  color: string
  vx: number
  vy: number
}

interface SparklesProps {
  children?: React.ReactNode
  className?: string
  /** How often new sparkles are created (ms). Lower = more sparkles. */
  interval?: number
  colors?: string[]
}

/**
 * Sparkles — animated particle burst overlay.
 * Wraps children and renders floating sparkle particles on top.
 * Adapted from Aceternity UI for RunMyCrew.
 */
function Sparkles({
  children,
  className,
  interval = 120,
  colors = ['var(--accent)', 'var(--ok)', '#fff', 'var(--accent-soft)'],
}: SparklesProps) {
  const [particles, setParticles] = useState<Particle[]>([])
  const containerRef = useRef<HTMLDivElement>(null)
  const counterRef = useRef(0)

  useEffect(() => {
    const timer = setInterval(() => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const id = counterRef.current++

      setParticles((prev) => [
        ...prev.slice(-18), // keep max 18
        {
          id,
          x: Math.random() * rect.width,
          y: Math.random() * rect.height,
          size: 2 + Math.random() * 4,
          color: colors[Math.floor(Math.random() * colors.length)],
          vx: (Math.random() - 0.5) * 80,
          vy: -(30 + Math.random() * 60),
        },
      ])
    }, interval)

    return () => clearInterval(timer)
  }, [interval, colors])

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {children}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <AnimatePresence>
          {particles.map((p) => (
            <motion.span
              key={p.id}
              className="absolute block rounded-full"
              initial={{ opacity: 1, x: p.x, y: p.y, scale: 1 }}
              animate={{
                opacity: 0,
                x: p.x + p.vx,
                y: p.y + p.vy,
                scale: 0.3,
              }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              style={{
                width: p.size,
                height: p.size,
                background: p.color,
                left: 0,
                top: 0,
              }}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}

/**
 * SparklesBurst — one-shot sparkle burst (for success states).
 * Renders particles once when `active` becomes true.
 */
function SparklesBurst({ active, className }: { active: boolean; className?: string }) {
  return active ? <Sparkles className={className} interval={60} /> : null
}

export { Sparkles, SparklesBurst }
