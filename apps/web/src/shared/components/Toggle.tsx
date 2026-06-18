import { type ChangeEvent } from 'react'
import { Switch } from '@/components/ui/switch'

interface ToggleProps {
  checked?: boolean
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
  className?: string
  disabled?: boolean
  'aria-label'?: string
}

export function Toggle({ checked = false, onChange, className, disabled = false, 'aria-label': ariaLabel }: ToggleProps) {
  const handleCheckedChange = (val: boolean) => {
    if (onChange) {
      const event = {
        target: {
          checked: val,
          type: 'checkbox',
        },
        currentTarget: {
          checked: val,
        },
      } as unknown as ChangeEvent<HTMLInputElement>
      onChange(event)
    }
  }

  return (
    <Switch
      checked={checked}
      onCheckedChange={handleCheckedChange}
      disabled={disabled}
      className={className}
      aria-label={ariaLabel}
    />
  )
}
