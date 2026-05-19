---
name: new-feature
description: "Scaffold a new frontend feature — directory structure, page component, React Query hooks, API client calls, and route registration. Usage: /new-feature"
---

# new-feature skill

Ask the user for:
1. **Feature name** — kebab-case (e.g. `tags`, `comments`, `webhooks`)
2. **What it shows** — brief description of the page/feature
3. **API endpoint** — the backend URL prefix (e.g. `/api/v1/tags`)
4. **Operations needed** — list, create, update, delete (which ones?)
5. **Route path** — where it lives in the app (e.g. `/settings/tags`, `/tags`)

## Files to create

### 1. API hooks — `apps/web/src/hooks/<feature-name>/queries.ts`

Follow the existing pattern in `apps/web/src/hooks/credentials/` and `apps/web/src/hooks/nodes/`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api/client'

const QUERY_KEY = ['<feature-name>']

// Types
export interface <ModelName> {
  id: string
  // ... fields matching backend <ModelName>Out schema
  created_at: string
  updated_at: string
}

// Queries
export function use<ModelName>s() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<'<model-plural>'>('/api/v1/<model-plural>/')
      return res.data
    },
  })
}

export function use<ModelName>(id: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: async () => {
      const res = await apiClient.get<'<ModelName>'>(`/api/v1/<model-plural>/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

// Mutations
export function useCreate<ModelName>() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<<ModelName>>) => {
      const res = await apiClient.post<'<ModelName>'>('/api/v1/<model-plural>/', data)
      return res.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdate<ModelName>() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<<ModelName>> & { id: string }) => {
      const res = await apiClient.put<'<ModelName>'>(`/api/v1/<model-plural>/${id}`, data)
      return res.data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDelete<ModelName>() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/v1/<model-plural>/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
```

### 2. Feature directory — `apps/web/src/features/<feature-name>/`

Create these files:

**`pages/<FeatureName>Page.tsx`** — main page component:
```tsx
import React from 'react'
// Import hooks, UI components etc.

export default function <FeatureName>Page() {
  return (
    <div>
      {/* page content */}
    </div>
  )
}
```

**`components/`** — sub-components specific to this feature (list, item, form, modal)

### 3. Route registration — `apps/web/src/app/router.tsx`

Add a lazy import and route. Check existing route patterns in that file and follow the same structure (usually inside a protected route wrapper).

## Checklist

- [ ] Hook file exports are named consistently (`use<ModelName>s`, `useCreate<ModelName>`, etc.)
- [ ] `QUERY_KEY` is unique and consistent across all hooks for this feature
- [ ] All mutations call `qc.invalidateQueries` on success
- [ ] Page component is default-exported (for lazy loading)
- [ ] Route is added inside the authenticated route wrapper
- [ ] Types match the backend `<ModelName>Out` Pydantic schema fields exactly
