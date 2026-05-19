---
name: new-ui-component
description: "Scaffold a new reusable UI component in components/ui/ following the project's component patterns — forwardRef, cn() for className merging, variant/size props, barrel export. Usage: /new-ui-component"
---

# new-ui-component skill

Ask the user for:
1. **Component name** — PascalCase (e.g. `Badge`, `Tabs`, `Popover`, `Card`)
2. **What it renders** — brief description
3. **Variants needed** — e.g. `default | primary | danger` or `sm | md | lg`
4. **Props** — list of props beyond variant/size/className/children
5. **Uses existing components?** — does it compose `Button`, `Tooltip`, `Modal`, etc.?

## Rules to follow

These are non-negotiable for every new component in this project:

1. **Use `cn()` from `@/lib/utils`** for className merging — never string concatenation
2. **Use `React.forwardRef`** if the component wraps a DOM element
3. **Use `var(--token-name)`** for colors — never hardcoded hex
4. **Export from `components/ui/index.ts`** barrel — add the new export there
5. **Export the Props interface** — name it `<ComponentName>Props`
6. **No default exports** — named exports only

## Template

```tsx
import React from 'react'
import { cn } from '@/lib/utils'

const variantClasses = {
  default:  '...uses var(--...) tokens...',
  primary:  '...',
  danger:   '...',
} as const

const sizeClasses = {
  sm: '...',
  md: '...',
  lg: '...',
} as const

export interface <ComponentName>Props extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof variantClasses
  size?: keyof typeof sizeClasses
  // additional props
}

export const <ComponentName> = React.forwardRef<HTMLDivElement, <ComponentName>Props>(({
  variant = 'default',
  size = 'md',
  className,
  children,
  ...props
}, ref) => (
  <div
    ref={ref}
    className={cn(
      // base classes
      variantClasses[variant],
      sizeClasses[size],
      className,
    )}
    {...props}
  >
    {children}
  </div>
))

<ComponentName>.displayName = '<ComponentName>'
```

## Design tokens to use

Reference these in className strings:
- Backgrounds: `bg-surface-{1-7}`, `bg-surface-editor`, `bg-surface-modal`
- Text: `text-text-primary`, `text-text-muted`, `text-text-placeholder`
- Borders: `border-border`, `border-border-strong`
- Brand: `bg-brand`, `text-brand`
- States: `hover:bg-surface-hover`, `bg-surface-active`

## After creating the file

Add to `apps/web/src/components/ui/index.ts`:
```typescript
export { <ComponentName> } from './<component-name>'
export type { <ComponentName>Props } from './<component-name>'
```
