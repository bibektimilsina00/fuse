---
description: Frontend rules for React/ReactFlow workflow editor
globs:
  - apps/web_v2/src/**
---

# Frontend rules

## Stack
- React 19, Vite, TypeScript, Tailwind, Zustand, TanStack Query, ReactFlow

## Patterns
- Logic in hooks (`use*.ts`), UI components are pure render — no business logic in JSX files
- Shared state: Zustand (`useWorkflowEditorStore`) — no prop-drilling deep state
- Server state: TanStack Query — no manual fetch/useEffect for API calls
- Colors: CSS variables only (`var(--token)`) — no hardcoded hex/rgb
- Reuse `shared/components/` (Button, Input, Modal, Spinner, Tooltip, etc.) — never re-implement

## ReactFlow specific
- `ReactFlowProvider` lives at page level (`WorkflowEditor.tsx`) — not inside canvas
- Node type checks forbidden inside `WorkflowNode` — use definition properties
- `onNodeClick` for inspector open, `onSelectionChange` for ID sync only
- Drag-and-drop: `dataTransfer.setData('application/reactflow', type)` pattern
