'use client'
import { cn } from '@/lib/cn'

interface BackgroundBeamsProps {
  className?: string
}

/**
 * BackgroundBeams — SVG-based animated light ray beams.
 * Ideal for auth pages and hero areas. Adapted from Aceternity UI.
 * Place as the first child of a `relative` container.
 */
function BackgroundBeams({ className }: BackgroundBeamsProps) {
  return (
    <div
      className={cn(
        'absolute inset-0 overflow-hidden pointer-events-none',
        className,
      )}
      aria-hidden="true"
    >
      <svg
        className="absolute inset-0 h-full w-full"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 800 800"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <radialGradient id="bgb-center" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.08" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>
          {/* Individual beam gradients */}
          {Array.from({ length: 8 }, (_, i) => (
            <linearGradient
              key={i}
              id={`bgb-beam-${i}`}
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
              gradientUnits="userSpaceOnUse"
              gradientTransform={`rotate(${i * 22.5 + 15}, 400, 400)`}
            >
              <stop offset="0%" stopColor="transparent" />
              <stop offset="40%" stopColor="var(--accent)" stopOpacity={0.04 + i * 0.005} />
              <stop offset="60%" stopColor="var(--accent)" stopOpacity={0.06 + i * 0.005} />
              <stop offset="100%" stopColor="transparent" />
            </linearGradient>
          ))}
        </defs>

        {/* Ambient glow */}
        <rect x="0" y="0" width="800" height="800" fill="url(#bgb-center)" />

        {/* Beams */}
        {Array.from({ length: 8 }, (_, i) => (
          <rect
            key={i}
            x="-200"
            y="390"
            width="1200"
            height="20"
            fill={`url(#bgb-beam-${i})`}
            style={{
              transformOrigin: '400px 400px',
              transform: `rotate(${i * 22.5}deg)`,
              opacity: 0.5 + (i % 3) * 0.2,
            }}
          />
        ))}

        {/* Soft center bloom */}
        <circle cx="400" cy="400" r="120" fill="var(--accent)" fillOpacity="0.03" />
        <circle cx="400" cy="400" r="60" fill="var(--accent)" fillOpacity="0.05" />
      </svg>
    </div>
  )
}

export { BackgroundBeams }
