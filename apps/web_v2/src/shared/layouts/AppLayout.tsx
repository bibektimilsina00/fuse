import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { WorkspaceSelector, useWorkspaces, useWorkspaceStore } from '@/features/workspaces'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useToast, useConfirm, Modal, Input, Button, Spinner, ColorPicker } from '@/shared/components'
import { useTheme } from '@/stores/theme'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { cn } from '@/lib/cn'
import { DndContext, useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import {
  useFolders,
  useCreateFolder,
  useUpdateFolder,
  useDeleteFolder,
  SidebarFolderItem,
} from '@/features/folders'
import {
  useWorkflows,
  useCreateWorkflow,
  useUpdateWorkflow,
  useDeleteWorkflow,
  useDuplicateWorkflow,
  useWorkflowDnD,
  SidebarWorkflowItem,
  WorkflowDragOverlay,
} from '@/features/workflows'

type NavGroup = {
  group: string
  isWorkflows?: boolean
  items?: { id: string; label: string; icon: React.FC<React.SVGProps<SVGSVGElement>>; count?: string; to: string }[]
}

const NAV: NavGroup[] = [
  {
    group: 'Workspace', items: [
      { id: 'home', label: 'Home', icon: Icons.Home, to: APP_ROUTES.DASHBOARD },
      { id: 'automations', label: 'Automations', icon: Icons.Flow, count: '47', to: APP_ROUTES.AUTOMATIONS },
      { id: 'templates', label: 'Templates', icon: Icons.Layers, to: APP_ROUTES.TEMPLATES },
    ],
  },
  {
    group: 'Operate', items: [
      { id: 'runs', label: 'Runs', icon: Icons.Activity, count: '1.2k', to: APP_ROUTES.RUNS },
      { id: 'schedules', label: 'Schedules', icon: Icons.Clock, count: '6', to: APP_ROUTES.SCHEDULES },
      { id: 'logs', label: 'Logs', icon: Icons.Terminal, to: APP_ROUTES.LOGS },
    ],
  },
  {
    group: 'Data', items: [
      { id: 'tables', label: 'Tables', icon: Icons.Table, count: '8', to: APP_ROUTES.TABLES },
      { id: 'files', label: 'Files', icon: Icons.Folder, count: '124', to: APP_ROUTES.FILES },
      { id: 'knowledge', label: 'Knowledge base', icon: Icons.Book, count: '8', to: APP_ROUTES.KNOWLEDGE },
      { id: 'variables', label: 'Variables', icon: Icons.Key, to: APP_ROUTES.VARIABLES },
    ],
  },
  {
    group: 'Integrations', items: [
      { id: 'connections', label: 'Connections', icon: Icons.Plug, count: '18', to: APP_ROUTES.CONNECTIONS },
    ],
  },
  { group: 'Workflows', isWorkflows: true },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const { toast } = useToast()
  const confirm = useConfirm()

  useWorkspaces() // bootstrap workspace list + auto-select

  const { currentWorkspace } = useWorkspaceStore()

  // Queries
  const { data: folders = [], isLoading: isLoadingFolders } = useFolders()
  const { data: workflows = [], isLoading: isLoadingWorkflows } = useWorkflows()

  // Mutations
  const createFolder = useCreateFolder()
  const updateFolder = useUpdateFolder()
  const deleteFolder = useDeleteFolder()

  const createWorkflow = useCreateWorkflow()
  const updateWorkflow = useUpdateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const duplicateWorkflow = useDuplicateWorkflow()

  const { theme, toggle: toggleTheme } = useTheme()
  const [collapsed, setCollapsed] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    Workspace: true, Operate: true, Workflows: true, Data: false, Integrations: false,
  })
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(null)

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if (e.key === '?') setShortcutsOpen(v => !v)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const {
    sensors,
    expandedFolders,
    rootWorkflows,
    activeWorkflowForOverlay,
    toggleFolder: toggleFolderDnD,
    handleDragStart,
    handleDragOver,
    handleDragEnd,
  } = useWorkflowDnD({ workflows, folders })

  const { setNodeRef: setRootNodeRef } = useDroppable({
    id: 'workflow-section-root',
    data: { isRoot: true },
  })

  // Modals state
  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false)
  const [createFolderName, setCreateFolderName] = useState('')
  const [folderParentId, setFolderParentId] = useState<string | null>(null)

  const [isRenameFolderOpen, setIsRenameFolderOpen] = useState(false)
  const [renameFolderId, setRenameFolderId] = useState('')
  const [renameFolderName, setRenameFolderName] = useState('')

  const [isCreateWorkflowOpen, setIsCreateWorkflowOpen] = useState(false)
  const [createWorkflowName, setCreateWorkflowName] = useState('')
  const [workflowFolderId, setWorkflowFolderId] = useState<string | null>(null)
  const [createWorkflowColor, setCreateWorkflowColor] = useState<string | null>(null)

  const [isRenameWorkflowOpen, setIsRenameWorkflowOpen] = useState(false)
  const [renameWorkflowId, setRenameWorkflowId] = useState('')
  const [renameWorkflowName, setRenameWorkflowName] = useState('')
  const [renameWorkflowColor, setRenameWorkflowColor] = useState<string | null>(null)

  const toggleGroup = (g: string) => setOpenGroups(s => ({ ...s, [g]: !s[g] }))
  const closeMenus = () => { setMenuOpen(null); setMenuPos(null) }
  const stopAndOpen = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    e.preventDefault()
    if (menuOpen === id) {
      setMenuOpen(null)
      setMenuPos(null)
    } else {
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
      setMenuPos({ top: rect.top, left: rect.right + 4 })
      setMenuOpen(id)
    }
  }

  const pageName = location.pathname.substring(1) || 'dashboard'
  const pageLabel = pageName.charAt(0).toUpperCase() + pageName.slice(1)

  const TOTAL_WFS = workflows.length

  const DropdownMenu = ({ id, children }: { id: string; children: React.ReactNode }) => {
    if (menuOpen !== id || !menuPos) return null
    return createPortal(
      <>
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
          onClick={e => { e.stopPropagation(); closeMenus() }}
        />
        <div
          className="w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100"
          style={{ position: 'fixed', top: menuPos.top, left: menuPos.left, zIndex: 9999 }}
          onClick={e => e.stopPropagation()}
        >
          {children}
        </div>
      </>,
      document.body
    )
  }

  return (
    <div className={cn("group/shell relative h-screen grid grid-cols-[244px_1fr] gap-[14px] z-10 data-[collapsed=true]:grid-cols-[64px_1fr]")} data-collapsed={collapsed}>
      <div className="dot-grid" />

      {/* ── Sidebar ── */}
      <aside className="relative h-[calc(100vh-28px)] my-[14px] ml-[14px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] flex flex-col overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] z-20">
        <div className="shrink-0 pt-[14px] px-[10px] pb-[12px] flex flex-col gap-[12px] border-b border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[14px] group-data-[collapsed=true]/shell:px-[8px] group-data-[collapsed=true]/shell:pb-[12px] group-data-[collapsed=true]/shell:gap-[10px]">
          <div className="flex items-center justify-between py-[2px] px-[6px] pb-[4px] group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:flex-col group-data-[collapsed=true]/shell:gap-[10px] group-data-[collapsed=true]/shell:px-[4px]">
            <span className="inline-flex items-center gap-[9px] text-[15px] font-semibold tracking-tight text-[var(--text)] group-data-[collapsed=true]/shell:gap-0">
              <span className="w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)]"><Icons.FuseMark style={{ width: 14, height: 14 }} /></span>
              <span className="inline group-data-[collapsed=true]/shell:hidden">fuse</span>
              <span className="font-mono text-[9.5px] tracking-[0.14em] uppercase text-[var(--text-faint)] border border-[var(--border-soft)] py-[2px] px-[6px] pb-[1px] rounded-[4px] ml-[6px] group-data-[collapsed=true]/shell:hidden">Beta</span>
            </span>
            <button
              className="w-[24px] h-[24px] rounded-[6px] text-[var(--text-faint)] inline-flex items-center justify-center hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]"
              onClick={() => setCollapsed(c => !c)}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <Icons.PanelOpen /> : <Icons.PanelClose />}
            </button>
          </div>

          <WorkspaceSelector />

          <div className="flex items-center gap-[8px] px-[10px] h-[34px] rounded-[9px] bg-[var(--bg)] border border-[var(--border-faint)] transition-colors duration-120 w-full min-w-0 hover:border-[var(--border-soft)] focus-within:border-[var(--border)] focus-within:bg-[var(--surface)] [&>svg]:w-[14px] [&>svg]:h-[14px] [&>svg]:text-[var(--text-faint)] [&>svg]:shrink-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:px-0 group-data-[collapsed=true]/shell:gap-0">
            <Icons.Search />
            <input placeholder="Search" className="bg-transparent border-none outline-none flex-1 min-w-0 text-[13px] text-[var(--text)] tracking-tight p-0 placeholder:text-[var(--text-faint)] group-data-[collapsed=true]/shell:hidden" />
            <span className="kbd group-data-[collapsed=true]/shell:hidden">⌘K</span>
          </div>
        </div>

        {/* Nav groups */}
        <div className="flex-1 min-h-0 overflow-y-auto pt-[8px] px-[10px] pb-[10px] flex flex-col gap-0 [&::-webkit-scrollbar]:hidden [scrollbar-width:none] group-data-[collapsed=true]/shell:px-[8px]">
          {NAV.map((section, gi) => {
            const open = openGroups[section.group]
            return (
              <div
                key={gi}
                className={cn(
                  "flex flex-col gap-[1px] pb-[4px] group-data-[collapsed=true]/shell:pb-[6px] group-data-[collapsed=true]/shell:border-t group-data-[collapsed=true]/shell:border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[6px] first:border-none first:pt-0",
                  !open && "pb-0",
                  section.isWorkflows && "relative"
                )}
              >
                <div className="flex items-center gap-[6px] pt-[8px] px-[10px] pb-[4px] font-mono text-[10px] tracking-widest uppercase text-[var(--text-dim)] font-medium cursor-pointer w-full text-left transition-colors duration-100 hover:text-[var(--text-mute)] group-data-[collapsed=true]/shell:hidden relative" onClick={() => toggleGroup(section.group)}>
                  <span className="inline-flex w-[12px] h-[12px] transition-transform duration-160 [&_svg]:w-[11px] [&_svg]:h-[11px]"><Icons.Caret /></span>
                  <span className="flex-1">{section.group}</span>

                  {section.isWorkflows && (
                    <>
                      <span className="font-mono text-[9.5px] text-[var(--text-faint)] ml-[4px] font-medium">{TOTAL_WFS}</span>
                      <button
                        className={cn(
                          "w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]",
                          menuOpen === 'group' && "bg-[var(--surface-2)] text-[var(--text)]"
                        )}
                        onClick={e => stopAndOpen(e, 'group')}
                        title="More"
                      >
                        <Icons.More />
                      </button>
                      <button
                        className="w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]"
                        title="New workflow"
                        onClick={e => {
                          e.stopPropagation()
                          setIsCreateWorkflowOpen(true)
                        }}
                      >
                        <Icons.Plus />
                      </button>
                      <DropdownMenu id="group">
                        <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0" onClick={e => {
                          e.stopPropagation()
                          closeMenus()
                          setIsCreateWorkflowOpen(true)
                        }}><Icons.Plus /> New workflow</button>
                        <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0" onClick={e => {
                          e.stopPropagation()
                          closeMenus()
                          setIsCreateFolderOpen(true)
                        }}><Icons.Folder /> Create folder</button>
                        <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0" onClick={e => {
                          e.stopPropagation()
                          closeMenus()
                          toast('Import feature not implemented yet', { variant: 'warn' })
                        }}><Icons.Doc /> Import workflow</button>
                        <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0" onClick={e => {
                          e.stopPropagation()
                          closeMenus()
                          toast('Export all feature not implemented yet', { variant: 'warn' })
                        }}><Icons.Download /> Export all</button>
                        <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
                        <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0" onClick={e => {
                          e.stopPropagation()
                          closeMenus()
                          toast('Sorting not implemented yet', { variant: 'warn' })
                        }}><Icons.Sort /> Sort A → Z</button>
                      </DropdownMenu>
                    </>
                  )}
                </div>

                {open && !section.isWorkflows && section.items?.map(n => (
                  <NavLink
                    key={n.id}
                    to={n.to}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-[10px] py-[7px] px-[10px] rounded-[8px] text-[13px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full font-medium no-underline relative hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[15px] [&_svg]:h-[15px] [&_svg]:text-current [&_svg]:opacity-85 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:p-[9px] group-data-[collapsed=true]/shell:gap-0",
                        isActive && n.to !== '#' && "bg-[var(--surface)] text-[var(--text)] group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)] before:content-[''] before:w-[3px] before:h-[14px] before:bg-[var(--text)] before:rounded-[0_2px_2px_0] before:absolute before:left-0 group-data-[collapsed=true]/shell:before:hidden"
                      )
                    }
                    title={n.label}
                  >
                    <n.icon />
                    <span className="flex-1 group-data-[collapsed=true]/shell:hidden">{n.label}</span>
                    {n.count && <span className="ml-auto font-mono text-[10.5px] text-[var(--text-faint)] font-medium group-data-[collapsed=true]/shell:hidden">{n.count}</span>}
                  </NavLink>
                ))}

                {open && section.isWorkflows && (
                  <DndContext
                    sensors={sensors}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDragEnd={handleDragEnd}
                  >
                    <div ref={setRootNodeRef} className="flex flex-col gap-[1px] group-data-[collapsed=true]/shell:hidden">
                      {isLoadingFolders || isLoadingWorkflows ? (
                        <div className="flex items-center justify-center py-4">
                          <Spinner />
                        </div>
                      ) : folders.length === 0 && workflows.length === 0 ? (
                        <div className="text-center py-3 text-[11px] text-[var(--text-mute)]">
                          No folders or workflows
                        </div>
                      ) : (
                        <>
                          {folders
                            .filter(f => !f.parent_id || !folders.some(p => p.id === f.parent_id))
                            .map(folder => (
                              <SidebarFolderItem
                                key={folder.id}
                                folder={folder}
                                allFolders={folders}
                                allWorkflows={workflows}
                                expandedFolders={expandedFolders}
                                toggleFolder={toggleFolderDnD}
                                openMenuId={menuOpen}
                                setOpenMenuId={setMenuOpen}
                                onCreateWorkflow={(folderId) => {
                                  setWorkflowFolderId(folderId)
                                  setIsCreateWorkflowOpen(true)
                                }}
                                onCreateSubfolder={(parentFolderId) => {
                                  setFolderParentId(parentFolderId)
                                  setIsCreateFolderOpen(true)
                                }}
                                onRenameFolder={(id, name) => {
                                  setRenameFolderId(id)
                                  setRenameFolderName(name)
                                  setIsRenameFolderOpen(true)
                                }}
                                onDeleteFolder={(id, name) => {
                                  confirm({
                                    title: 'Delete Folder',
                                    message: `Are you sure you want to delete the folder "${name}"? This will not delete its workflows, they will be moved to root.`,
                                    confirmText: 'Delete',
                                    variant: 'danger',
                                  }).then((confirmed) => {
                                    if (confirmed) {
                                      deleteFolder.mutate(id, {
                                        onSuccess: () => {
                                          toast('Folder deleted successfully', { variant: 'ok' })
                                        },
                                        onError: () => {
                                          toast('Failed to delete folder', { variant: 'err' })
                                        }
                                      })
                                    }
                                  })
                                }}
                                onRenameWorkflow={(id, name, color) => {
                                  setRenameWorkflowId(id)
                                  setRenameWorkflowName(name)
                                  setRenameWorkflowColor(color)
                                  setIsRenameWorkflowOpen(true)
                                }}
                                onDeleteWorkflow={(id, name) => {
                                  confirm({
                                    title: 'Delete Workflow',
                                    message: `Are you sure you want to delete the workflow "${name}"?`,
                                    confirmText: 'Delete',
                                    variant: 'danger',
                                  }).then((confirmed) => {
                                    if (confirmed) {
                                      deleteWorkflow.mutate(id, {
                                        onSuccess: () => {
                                          toast('Workflow deleted successfully', { variant: 'ok' })
                                        },
                                        onError: () => {
                                          toast('Failed to delete workflow', { variant: 'err' })
                                        }
                                      })
                                    }
                                  })
                                }}
                                onDuplicateWorkflow={(id) => {
                                  duplicateWorkflow.mutate(id, {
                                    onSuccess: () => {
                                      toast('Workflow duplicated successfully', { variant: 'ok' })
                                    },
                                    onError: () => {
                                      toast('Failed to duplicate workflow', { variant: 'err' })
                                    }
                                  })
                                }}
                                onToggleWorkflowActive={(id, isActive) => {
                                  updateWorkflow.mutate({ id, is_active: isActive }, {
                                    onSuccess: () => {
                                      toast(isActive ? 'Workflow activated' : 'Workflow paused', { variant: 'ok' })
                                    },
                                    onError: () => {
                                      toast('Failed to update workflow state', { variant: 'err' })
                                    }
                                  })
                                }}
                              />
                            ))}

                          {rootWorkflows.length > 0 && (
                            <SortableContext
                              items={rootWorkflows.map(w => `workflow-${w.id}`)}
                              strategy={verticalListSortingStrategy}
                            >
                              {rootWorkflows.map(w => (
                                <SidebarWorkflowItem
                                  key={w.id}
                                  workflow={w}
                                  onRename={(id, name, color) => {
                                    setRenameWorkflowId(id)
                                    setRenameWorkflowName(name)
                                    setRenameWorkflowColor(color)
                                    setIsRenameWorkflowOpen(true)
                                  }}
                                  onDelete={(id, name) => {
                                    confirm({
                                      title: 'Delete Workflow',
                                      message: `Are you sure you want to delete the workflow "${name}"?`,
                                      confirmText: 'Delete',
                                      variant: 'danger',
                                    }).then((confirmed) => {
                                      if (confirmed) {
                                        deleteWorkflow.mutate(id, {
                                          onSuccess: () => {
                                            toast('Workflow deleted successfully', { variant: 'ok' })
                                          },
                                          onError: () => {
                                            toast('Failed to delete workflow', { variant: 'err' })
                                          }
                                        })
                                      }
                                    })
                                  }}
                                  onDuplicate={(id) => {
                                    duplicateWorkflow.mutate(id, {
                                      onSuccess: () => {
                                        toast('Workflow duplicated successfully', { variant: 'ok' })
                                      },
                                      onError: () => {
                                        toast('Failed to duplicate workflow', { variant: 'err' })
                                      }
                                    })
                                  }}
                                  onToggleActive={(id, isActive) => {
                                    updateWorkflow.mutate({ id, is_active: isActive }, {
                                      onSuccess: () => {
                                        toast(isActive ? 'Workflow activated' : 'Workflow paused', { variant: 'ok' })
                                      },
                                      onError: () => {
                                        toast('Failed to update workflow state', { variant: 'err' })
                                      }
                                    })
                                  }}
                                  openMenuId={menuOpen}
                                  setOpenMenuId={setMenuOpen}
                                />
                              ))}
                            </SortableContext>
                          )}
                        </>
                      )}
                    </div>
                    <WorkflowDragOverlay activeWorkflow={activeWorkflowForOverlay} />
                  </DndContext>
                )}
              </div>
            )
          })}
        </div>

        <div className="shrink-0 p-[8px] border-t border-[var(--border-faint)] flex gap-[4px] group-data-[collapsed=true]/shell:hidden">
          <button className="flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]" type="button"><Icons.Help /> Help &amp; docs</button>
          <button className="flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]" type="button"><Icons.Feedback /> Feedback</button>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className="relative overflow-hidden h-screen pt-[14px] pr-[14px] pb-[14px] pl-0 flex flex-col">
        <div className="bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] h-full overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] flex flex-col flex-1 min-h-0">
          <header className="flex items-center justify-between py-[14px] px-[22px] border-b border-[var(--border-faint)] shrink-0">
            <div className="flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]">
              <span>{currentWorkspace?.name ?? 'My workspace'}</span>
              <span className="text-[var(--text-dim)]">/</span>
              <span className="text-[var(--text)] font-medium">{pageLabel}</span>
            </div>

            <div className="flex items-center gap-[6px]">
              <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Activity"><Icons.Activity /></button>
              <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Keyboard shortcuts" onClick={() => setShortcutsOpen(true)}><Icons.Cmd /></button>

              <div className="relative">
                <button
                  className={cn(
                    "w-[28px] h-[28px] rounded-[8px] bg-[var(--surface-3)] border border-[var(--border-soft)] cursor-pointer inline-flex items-center justify-center text-[11px] font-semibold text-[var(--text)] tracking-tight bg-cover bg-center transition-colors duration-120 hover:border-[var(--border)]",
                    profileOpen && "bg-[var(--surface-2)] text-[var(--text)]"
                  )}
                  onClick={() => setProfileOpen(v => !v)}
                  aria-label="Account"
                  style={{
                    backgroundImage: user?.avatar_url ? `url(${user.avatar_url})` : undefined,
                  }}
                >
                  {!user?.avatar_url && (user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()}
                </button>

                {profileOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
                    <div className="absolute top-[calc(100%+8px)] right-0 w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[13px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] z-50 animate-in fade-in slide-in-from-top-2">
                      <div className="flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]">
                        <span className="w-[32px] h-[32px] rounded-[9px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[13px] font-semibold text-[var(--text)] shrink-0">
                          {(user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()}
                        </span>
                        <span className="flex flex-col gap-[1px] min-w-0">
                          <span className="text-[13px] font-medium">{user?.full_name || 'Anonymous'}</span>
                          <span className="text-[11px] text-[var(--text-faint)] font-mono">{user?.email}</span>
                        </span>
                      </div>

                      <NavLink
                        to={APP_ROUTES.SETTINGS}
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => setProfileOpen(false)}
                      >
                        <Icons.Settings /> Account settings <span className="kbd">⌘,</span>
                      </NavLink>

                      <NavLink
                        to={APP_ROUTES.WORKSPACE_SETTINGS}
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => setProfileOpen(false)}
                      >
                        <Icons.Settings /> Workspace settings
                      </NavLink>
                      <NavLink
                        to={APP_ROUTES.CONNECTIONS}
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => setProfileOpen(false)}
                      >
                        <Icons.Plug /> Connected apps
                      </NavLink>
                      <NavLink
                        to={APP_ROUTES.RUNS}
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => setProfileOpen(false)}
                      >
                        <Icons.Activity /> Run usage
                      </NavLink>
                      <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
                      <button
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={toggleTheme}
                      >
                        <Icons.Moon /> Appearance
                        <span className="ml-auto font-mono text-[10.5px] text-[var(--text-faint)] capitalize">{theme}</span>
                      </button>
                      <button
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => { setProfileOpen(false); setShortcutsOpen(true) }}
                      >
                        <Icons.Cmd /> Keyboard shortcuts <span className="ml-auto kbd">?</span>
                      </button>
                      <button
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => { setProfileOpen(false); window.open('https://docs.fuse.io', '_blank', 'noopener') }}
                      >
                        <Icons.Doc /> Documentation
                      </button>
                      <button
                        className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
                        onClick={() => { setProfileOpen(false); setFeedbackOpen(true) }}
                      >
                        <Icons.Feedback /> Send feedback
                      </button>
                      <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
                      <button className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0 text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]" onClick={() => { setProfileOpen(false); logout() }}>
                        <Icons.SignOut /> Sign out
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </header>

          <div className="flex-1 min-h-0 overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
            <Outlet />
          </div>
        </div>
      </div>

      {/* ── Keyboard shortcuts modal ── */}
      {shortcutsOpen && createPortal(
        <>
          <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={() => setShortcutsOpen(false)} />
          <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[520px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)]">
              <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">Keyboard shortcuts</h3>
              <button onClick={() => setShortcutsOpen(false)} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
            </div>
            <div className="p-5 grid grid-cols-2 gap-x-8 gap-y-0">
              {[
                {
                  group: 'Navigation', items: [
                    { keys: ['⌘', 'K'], label: 'Command palette' },
                    { keys: ['⌘', ','], label: 'Account settings' },
                    { keys: ['?'], label: 'Keyboard shortcuts' },
                    { keys: ['G', 'H'], label: 'Go to Home' },
                    { keys: ['G', 'A'], label: 'Go to Automations' },
                    { keys: ['G', 'R'], label: 'Go to Runs' },
                  ]
                },
                {
                  group: 'Workflows', items: [
                    { keys: ['⌘', 'N'], label: 'New automation' },
                    { keys: ['⌘', 'Enter'], label: 'Run workflow' },
                    { keys: ['⌘', 'S'], label: 'Save workflow' },
                    { keys: ['⌘', 'Z'], label: 'Undo' },
                    { keys: ['⌘', '⇧', 'Z'], label: 'Redo' },
                    { keys: ['Esc'], label: 'Close / cancel' },
                  ]
                },
              ].map(section => (
                <div key={section.group} className="flex flex-col gap-1 pb-4">
                  <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)] mb-2">{section.group}</span>
                  {section.items.map(item => (
                    <div key={item.label} className="flex items-center justify-between py-1.5">
                      <span className="text-[13px] text-[var(--text-mute)]">{item.label}</span>
                      <div className="flex items-center gap-1">
                        {item.keys.map((k, i) => (
                          <span key={i} className="kbd">{k}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </>,
        document.body
      )}

      {/* ── Feedback modal ── */}
      {feedbackOpen && createPortal(
        <>
          <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={() => { setFeedbackOpen(false); setFeedbackSent(false); setFeedbackText('') }} />
          <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[420px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] p-6 flex flex-col gap-5 shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">
            {feedbackSent ? (
              <div className="flex flex-col items-center gap-3 py-4 text-center">
                <div className="w-[44px] h-[44px] rounded-full bg-[oklch(0.78_0.14_145/0.14)] flex items-center justify-center">
                  <Icons.Check className="w-[20px] h-[20px] text-[var(--ok)]" />
                </div>
                <h3 className="text-[15px] font-semibold text-[var(--text)]">Thanks for your feedback!</h3>
                <p className="text-[13px] text-[var(--text-faint)]">We read every submission and use it to improve fuse.</p>
                <button
                  onClick={() => { setFeedbackOpen(false); setFeedbackSent(false); setFeedbackText('') }}
                  className="mt-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors"
                >
                  Close
                </button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">Send feedback</h3>
                  <button onClick={() => setFeedbackOpen(false)} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
                </div>
                <p className="text-[12.5px] text-[var(--text-faint)] -mt-2">Found a bug? Have a suggestion? We'd love to hear it.</p>
                <textarea
                  value={feedbackText}
                  onChange={e => setFeedbackText(e.target.value)}
                  placeholder="Describe what you're experiencing or what you'd like to see..."
                  rows={5}
                  className="w-full bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] px-4 py-3 text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none resize-none focus:border-[var(--border)] transition-colors"
                />
                <div className="flex items-center justify-end gap-3">
                  <button
                    onClick={() => setFeedbackOpen(false)}
                    className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => { if (feedbackText.trim()) setFeedbackSent(true) }}
                    disabled={!feedbackText.trim()}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default"
                  >
                    <Icons.Feedback className="w-[13px] h-[13px]" />
                    Send feedback
                  </button>
                </div>
              </>
            )}
          </div>
        </>,
        document.body
      )}

      {/* ── Modals ── */}
      <Modal
        open={isCreateFolderOpen}
        onClose={() => {
          setIsCreateFolderOpen(false)
          setCreateFolderName('')
          setFolderParentId(null)
        }}
        title="Create Folder"
      >
        <form onSubmit={(e) => {
          e.preventDefault()
          if (!createFolderName.trim()) return
          createFolder.mutate({ name: createFolderName, parentId: folderParentId }, {
            onSuccess: () => {
              toast('Folder created successfully', { variant: 'ok' })
              setIsCreateFolderOpen(false)
              setCreateFolderName('')
              setFolderParentId(null)
            },
            onError: () => {
              toast('Failed to create folder', { variant: 'err' })
            }
          })
        }} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Folder Name</label>
            <Input
              value={createFolderName}
              onChange={e => setCreateFolderName(e.target.value)}
              placeholder="e.g. Sales, Marketing"
              autoFocus
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
            <Button variant="secondary" type="button" size="sm" onClick={() => {
              setIsCreateFolderOpen(false)
              setCreateFolderName('')
              setFolderParentId(null)
            }}>Cancel</Button>
            <Button variant="primary" type="submit" size="sm" disabled={createFolder.isPending || !createFolderName.trim()}>
              {createFolder.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={isRenameFolderOpen}
        onClose={() => {
          setIsRenameFolderOpen(false)
          setRenameFolderId('')
          setRenameFolderName('')
        }}
        title="Rename Folder"
      >
        <form onSubmit={(e) => {
          e.preventDefault()
          if (!renameFolderName.trim()) return
          updateFolder.mutate({ id: renameFolderId, name: renameFolderName }, {
            onSuccess: () => {
              toast('Folder renamed successfully', { variant: 'ok' })
              setIsRenameFolderOpen(false)
              setRenameFolderId('')
              setRenameFolderName('')
            },
            onError: () => {
              toast('Failed to rename folder', { variant: 'err' })
            }
          })
        }} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">New Name</label>
            <Input
              value={renameFolderName}
              onChange={e => setRenameFolderName(e.target.value)}
              placeholder="New name..."
              autoFocus
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
            <Button variant="secondary" type="button" size="sm" onClick={() => {
              setIsRenameFolderOpen(false)
              setRenameFolderId('')
              setRenameFolderName('')
            }}>Cancel</Button>
            <Button variant="primary" type="submit" size="sm" disabled={updateFolder.isPending || !renameFolderName.trim()}>
              {updateFolder.isPending ? 'Saving...' : 'Rename'}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={isCreateWorkflowOpen}
        onClose={() => {
          setIsCreateWorkflowOpen(false)
          setCreateWorkflowName('')
          setWorkflowFolderId(null)
          setCreateWorkflowColor(null)
        }}
        title="Create Workflow"
      >
        <form onSubmit={(e) => {
          e.preventDefault()
          createWorkflow.mutate({
            name: createWorkflowName,
            folderId: workflowFolderId,
            color: createWorkflowColor
          }, {
            onSuccess: () => {
              toast('Workflow created successfully', { variant: 'ok' })
              setIsCreateWorkflowOpen(false)
              setCreateWorkflowName('')
              setWorkflowFolderId(null)
              setCreateWorkflowColor(null)
            },
            onError: () => {
              toast('Failed to create workflow', { variant: 'err' })
            }
          })
        }} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Workflow Name (Optional)</label>
            <Input
              value={createWorkflowName}
              onChange={e => setCreateWorkflowName(e.target.value)}
              placeholder="Leave empty for a cool random name"
              autoFocus
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Workflow Color (Optional)</label>
            <ColorPicker
              value={createWorkflowColor}
              onChange={setCreateWorkflowColor}
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
            <Button variant="secondary" type="button" size="sm" onClick={() => {
              setIsCreateWorkflowOpen(false)
              setCreateWorkflowName('')
              setWorkflowFolderId(null)
              setCreateWorkflowColor(null)
            }}>Cancel</Button>
            <Button variant="primary" type="submit" size="sm" disabled={createWorkflow.isPending}>
              {createWorkflow.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={isRenameWorkflowOpen}
        onClose={() => {
          setIsRenameWorkflowOpen(false)
          setRenameWorkflowId('')
          setRenameWorkflowName('')
          setRenameWorkflowColor(null)
        }}
        title="Workflow Settings"
      >
        <form onSubmit={(e) => {
          e.preventDefault()
          if (!renameWorkflowName.trim()) return
          updateWorkflow.mutate({ id: renameWorkflowId, name: renameWorkflowName, color: renameWorkflowColor }, {
            onSuccess: () => {
              toast('Workflow updated successfully', { variant: 'ok' })
              setIsRenameWorkflowOpen(false)
              setRenameWorkflowId('')
              setRenameWorkflowName('')
              setRenameWorkflowColor(null)
            },
            onError: () => {
              toast('Failed to update workflow settings', { variant: 'err' })
            }
          })
        }} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">New Name</label>
            <Input
              value={renameWorkflowName}
              onChange={e => setRenameWorkflowName(e.target.value)}
              placeholder="New name..."
              autoFocus
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Workflow Color</label>
            <ColorPicker
              value={renameWorkflowColor}
              onChange={setRenameWorkflowColor}
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
            <Button variant="secondary" type="button" size="sm" onClick={() => {
              setIsRenameWorkflowOpen(false)
              setRenameWorkflowId('')
              setRenameWorkflowName('')
              setRenameWorkflowColor(null)
            }}>Cancel</Button>
            <Button variant="primary" type="submit" size="sm" disabled={updateWorkflow.isPending || !renameWorkflowName.trim()}>
              {updateWorkflow.isPending ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
