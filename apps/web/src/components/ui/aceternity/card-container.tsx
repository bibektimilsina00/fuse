'use client'

import { useRef, useState } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'
import { cn } from '@/lib/cn'

interface CardContainerProps {
  children: React.ReactNode
  className?: string
  containerClassName?: string
}

/**
 * CardContainer — 3D perspective tilt on mouse hover.
 * Wrap content in `<CardBody>` for the tilt to apply correctly.
 * Adapted from Aceternity UI (CSS perspective + framer-motion transform).
 */
function CardContainer({ children, className, containerClassName }: CardContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [, setIsMouseEntered] = useState(false)

  const mouseX = useSpring(0, { stiffness: 200, damping: 20 })
  const mouseY = useSpring(0, { stiffness: 200, damping: 20 })

  const rotateX = useTransform(mouseY, [-0.5, 0.5], ['10deg', '-10deg'])
  const rotateY = useTransform(mouseX, [-0.5, 0.5], ['-10deg', '10deg'])

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    mouseX.set(x)
    mouseY.set(y)
  }

  const handleMouseLeave = () => {
    mouseX.set(0)
    mouseY.set(0)
    setIsMouseEntered(false)
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsMouseEntered(true)}
      onMouseLeave={handleMouseLeave}
      className={cn('flex items-center justify-center', containerClassName)}
      style={{ perspective: '800px' }}
    >
      <motion.div
        style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
        className={cn('relative', className)}
      >
        {children}
      </motion.div>
    </div>
  )
}

interface CardBodyProps {
  children: React.ReactNode
  className?: string
}

/**
 * CardBody — inner wrapper for 3D content inside CardContainer.
 */
function CardBody({ children, className }: CardBodyProps) {
  return (
    <div
      className={cn('[transform-style:preserve-3d] [&>*]:[transform-style:preserve-3d]', className)}
    >
      {children}
    </div>
  )
}

interface CardItemProps {
  as?: React.ElementType
  children: React.ReactNode
  className?: string
  /** Z-axis translation in px — higher = more "floating". */
  translateZ?: number | string
}

/**
 * CardItem — an element within the 3D card that floats at a specific z depth.
 */
function CardItem({ as: Tag = 'div', children, className, translateZ = 0 }: CardItemProps) {
  return (
    <Tag
      className={cn('', className)}
      style={{ transform: `translateZ(${translateZ}px)` }}
    >
      {children}
    </Tag>
  )
}

export { CardContainer, CardBody, CardItem }
