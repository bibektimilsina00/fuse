import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

interface TooltipProps {
  content: React.ReactNode
  children: React.ReactElement
  side?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
  disabled?: boolean
  delay?: number
}

export const Tooltip: React.FC<TooltipProps> = ({ 
  content, 
  children, 
  side: preferredSide = 'top', 
  className,
  disabled = false,
  delay = 500
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [isPositioned, setIsPositioned] = useState(false)
  const [computedSide, setComputedSide] = useState(preferredSide)
  const [coords, setCoords] = useState({ top: 0, left: 0 })
  const [arrowCoords, setArrowCoords] = useState({ top: 0, left: 0 })
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const showTooltip = () => {
    if (disabled) return
    timerRef.current = setTimeout(() => setIsVisible(true), delay)
  }

  const hideTooltip = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setIsVisible(false)
    setIsPositioned(false)
  }

  // Collision detection & auto-shift with Portal coords
  useEffect(() => {
    if (isVisible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight

      let finalSide = preferredSide

      // 1. Vertical Flipping
      if (preferredSide === 'top' && triggerRect.top < tooltipRect.height + 12) {
        finalSide = 'bottom'
      } else if (preferredSide === 'bottom' && triggerRect.bottom + tooltipRect.height + 12 > viewportHeight) {
        finalSide = 'top'
      }

      // 2. Horizontal Flipping
      if (preferredSide === 'left' && triggerRect.left < tooltipRect.width + 12) {
        finalSide = 'right'
      } else if (preferredSide === 'right' && triggerRect.right + tooltipRect.width + 12 > viewportWidth) {
        finalSide = 'left'
      }

      setComputedSide(finalSide)

      // 3. Absolute Positioning Math
      let top = 0
      let left = 0

      const triggerCenterH = triggerRect.left + triggerRect.width / 2
      const triggerCenterV = triggerRect.top + triggerRect.height / 2

      if (finalSide === 'top') {
        top = triggerRect.top - tooltipRect.height - 8
        left = triggerCenterH - tooltipRect.width / 2
      } else if (finalSide === 'bottom') {
        top = triggerRect.bottom + 8
        left = triggerCenterH - tooltipRect.width / 2
      } else if (finalSide === 'left') {
        top = triggerCenterV - tooltipRect.height / 2
        left = triggerRect.left - tooltipRect.width - 8
      } else if (finalSide === 'right') {
        top = triggerCenterV - tooltipRect.height / 2
        left = triggerRect.right + 8
      }

      // 4. Boundary Shifting (Horizontal)
      let aTop: number
      let aLeft: number

      if (finalSide === 'top' || finalSide === 'bottom') {
        if (left < 8) left = 8
        if (left + tooltipRect.width > viewportWidth - 8) left = viewportWidth - tooltipRect.width - 8
        
        // Arrow stays pinned to trigger
        aLeft = triggerCenterH - left
        aTop = finalSide === 'top' ? tooltipRect.height : 0
      } else {
        // Vertical boundary shifting
        if (top < 8) top = 8
        if (top + tooltipRect.height > viewportHeight - 8) top = viewportHeight - tooltipRect.height - 8
        
        aTop = triggerCenterV - top
        aLeft = finalSide === 'left' ? tooltipRect.width : 0
      }

      setCoords({ top, left })
      setArrowCoords({ top: aTop, left: aLeft })
      setIsPositioned(true)
    }
  }, [isVisible, preferredSide])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  return (
    <>
      <div 
        ref={triggerRef}
        className="relative inline-flex items-center"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
      >
        {children}
      </div>
      {isVisible && createPortal(
        <div 
          ref={tooltipRef}
          className={cn(
            "fixed z-[9999] px-1.5 py-0.5 text-[11px] font-medium text-black bg-white border border-gray-200 rounded shadow-2xl whitespace-nowrap pointer-events-none transition-[opacity,transform] duration-150 ease-out",
            isPositioned ? "animate-in fade-in zoom-in-95 opacity-100 visible" : "opacity-0 invisible",
            computedSide === 'top' && "origin-bottom",
            computedSide === 'bottom' && "origin-top",
            computedSide === 'left' && "origin-right",
            computedSide === 'right' && "origin-left",
            className
          )}
          style={{ 
            top: coords.top, 
            left: coords.left
          }}
        >
          {content}
          {/* Subtle Arrow */}
          <div 
            className={cn(
              "absolute w-1.5 h-1.5 bg-white border-gray-200 rotate-45",
              computedSide === 'top' && "border-b border-r",
              computedSide === 'bottom' && "border-t border-l",
              computedSide === 'left' && "border-t border-r",
              computedSide === 'right' && "border-b border-l"
            )} 
            style={{ 
              top: arrowCoords.top,
              left: arrowCoords.left,
              transform: `translate(-50%, -50%) rotate(45deg)`
            }}
          />
        </div>,
        document.body
      )}
    </>
  )
}
