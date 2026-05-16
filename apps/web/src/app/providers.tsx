import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfirmProvider } from '@/components/ui/confirm-modal'
import { useTheme } from '@/hooks/use-theme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Applies theme class to <html> at the top of the tree
function ThemeApplier() {
  useTheme()
  return null
}

export const Providers: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfirmProvider>
        <ThemeApplier />
        {children}
      </ConfirmProvider>
    </QueryClientProvider>
  )
}
