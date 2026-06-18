import { Slot } from '@radix-ui/react-slot'
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { buttonVariants, type ButtonVariantProps } from './button.variants'
import { Spinner } from '@/shared/components/Spinner'

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    ButtonVariantProps {
  /** Render as a different element (e.g. `<a>`) while keeping button styles. */
  asChild?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  loading?: boolean
}

/**
 * Fuse Button — built on CVA + Radix Slot.
 * Supports all legacy variants and options from the original Button.tsx.
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, leftIcon, rightIcon, loading, disabled, children, ...props }, ref) => {
    if (asChild) {
      return (
        <Slot
          ref={ref}
          className={cn(buttonVariants({ variant, size, className }))}
          {...props}
        >
          {children}
        </Slot>
      )
    }

    const isIcon = variant === 'icon' || variant === 'icon-sm'

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      >
        {loading ? (
          <Spinner size={isIcon || size === 'sm' ? 'xs' : 'sm'} className="shrink-0" />
        ) : (
          leftIcon
        )}
        {children}
        {!loading && rightIcon}
      </button>
    )
  },
)

Button.displayName = 'Button'

export { Button }

