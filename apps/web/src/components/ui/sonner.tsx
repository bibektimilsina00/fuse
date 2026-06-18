import { Toaster as SonnerToaster } from 'sonner'

/**
 * Fuse Toaster — drop-in sonner wrapper with Fuse theme tokens.
 * Place once in the app root (App.tsx) to replace the previous ToastProvider.
 */
function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast:
            'group toast bg-surface border border-border-faint text-text shadow-dropdown rounded-[10px] font-ui text-sm',
          description: 'text-text-mute text-xs',
          actionButton: 'bg-accent text-white text-xs px-3 py-1 rounded-[6px] font-medium',
          cancelButton: 'bg-surface-2 text-text-mute text-xs px-3 py-1 rounded-[6px] font-medium',
          success: 'border-ok/30 [&_[data-icon]]:text-ok',
          error:   'border-err/30 [&_[data-icon]]:text-err',
          warning: 'border-warn/30 [&_[data-icon]]:text-warn',
          info:    'border-accent/30 [&_[data-icon]]:text-accent',
        },
      }}
      expand
      richColors={false}
    />
  )
}

export { Toaster }
