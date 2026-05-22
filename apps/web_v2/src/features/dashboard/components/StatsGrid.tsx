import React from 'react'
import { Icons } from '@/shared/components'
import { Sparkline } from './Sparkline'

export interface StatItem {
  label: string
  value: string
  unit: string
  delta: string
  deltaDir: 'up' | 'down' | 'flat'
  spark: number[]
  icon: React.ReactNode
}

const defaultStats: StatItem[] = [
  {
    label: 'Runs today',
    value: '1,284',
    unit: '',
    delta: '+18%',
    deltaDir: 'up',
    spark: [4, 5, 3, 6, 4, 7, 8, 6, 9, 11, 9, 12],
    icon: <Icons.Activity className="w-3.5 h-3.5" />,
  },
  {
    label: 'Success rate',
    value: '99.2',
    unit: '%',
    delta: '+0.4pp',
    deltaDir: 'up',
    spark: [98, 97.8, 98.2, 98.5, 98.6, 99, 99.1, 99.2, 99.1, 99.2, 99.2, 99.2],
    icon: <Icons.Check className="w-3.5 h-3.5" />,
  },
  {
    label: 'Time saved',
    value: '14.2',
    unit: 'hr',
    delta: '+2.1hr',
    deltaDir: 'up',
    spark: [6, 7, 8, 8, 9, 10, 11, 12, 13, 13, 14, 14.2],
    icon: <Icons.Clock className="w-3.5 h-3.5" />,
  },
  {
    label: 'Active steps',
    value: '312',
    unit: '',
    delta: '-4',
    deltaDir: 'down',
    spark: [340, 338, 336, 334, 330, 324, 320, 318, 316, 314, 313, 312],
    icon: <Icons.Layers className="w-3.5 h-3.5" />,
  },
]

interface StatsGridProps {
  items?: StatItem[]
}

export function StatsGrid({ items = defaultStats }: StatsGridProps) {
  return (
    <div className="stats">
      {items.map((s, i) => (
        <div key={i} className="stat">
          <span className="stat-label">
            {s.icon}
            <span>{s.label}</span>
          </span>
          <span className="stat-value">
            {s.value}
            {s.unit && <span className="unit">{s.unit}</span>}
          </span>
          <span className={`stat-delta ${s.deltaDir}`}>
            {s.deltaDir === 'up' ? '↑' : s.deltaDir === 'down' ? '↓' : '—'} {s.delta}
          </span>
          <Sparkline
            data={s.spark}
            color={s.deltaDir === 'down' ? 'oklch(0.70 0.18 22)' : 'oklch(0.78 0.14 145)'}
          />
        </div>
      ))}
    </div>
  )
}
