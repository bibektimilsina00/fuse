import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type EditorTab = 'copilot' | 'library' | 'config' | 'logs' | 'test'
export type PanelZone = 'right' | 'bottom'

const TAB_LOCKED_ZONES: Partial<Record<EditorTab, PanelZone>> = {
  logs: 'bottom',
}

const DEFAULT_ZONES: Record<EditorTab, PanelZone> = {
  copilot: 'right',
  library: 'right',
  config: 'right',
  test: 'right',
  logs: 'bottom',
}

const MIN_BOTTOM_HEIGHT = 140
const MAX_BOTTOM_HEIGHT = 640
const DEFAULT_BOTTOM_HEIGHT = 260

interface EditorLayoutState {
  panelZones: Record<EditorTab, PanelZone>
  rightActiveTab: EditorTab
  bottomActiveTab: EditorTab
  rightOpen: boolean
  bottomOpen: boolean
  bottomHeight: number

  setRightActiveTab: (tab: EditorTab) => void
  setBottomActiveTab: (tab: EditorTab) => void
  setZoneOpen: (zone: PanelZone, open: boolean) => void
  toggleZone: (zone: PanelZone) => void
  setBottomHeight: (px: number) => void
  moveTabToZone: (tab: EditorTab, zone: PanelZone) => void
  focusTab: (tab: EditorTab) => void
  closeTabPanel: (tab: EditorTab) => void
  tabsInZone: (zone: PanelZone) => EditorTab[]
}

export const useEditorLayoutStore = create<EditorLayoutState>()(
  persist(
    (set, get) => ({
      panelZones: { ...DEFAULT_ZONES },
      rightActiveTab: 'copilot',
      bottomActiveTab: 'logs',
      rightOpen: true,
      bottomOpen: false,
      bottomHeight: DEFAULT_BOTTOM_HEIGHT,

      setRightActiveTab: (rightActiveTab) => set({ rightActiveTab, rightOpen: true }),
      setBottomActiveTab: (bottomActiveTab) => set({ bottomActiveTab, bottomOpen: true }),

      setZoneOpen: (zone, open) =>
        set(zone === 'right' ? { rightOpen: open } : { bottomOpen: open }),

      toggleZone: (zone) =>
        set((s) =>
          zone === 'right' ? { rightOpen: !s.rightOpen } : { bottomOpen: !s.bottomOpen },
        ),

      setBottomHeight: (px) =>
        set({
          bottomHeight: Math.min(MAX_BOTTOM_HEIGHT, Math.max(MIN_BOTTOM_HEIGHT, Math.round(px))),
        }),

      moveTabToZone: (tab, zone) => {
        const lock = TAB_LOCKED_ZONES[tab]
        if (lock && lock !== zone) return
        const s = get()
        if (s.panelZones[tab] === zone) return
        set({
          panelZones: { ...s.panelZones, [tab]: zone },
          ...(zone === 'right'
            ? { rightActiveTab: tab, rightOpen: true }
            : { bottomActiveTab: tab, bottomOpen: true }),
        })
      },

      focusTab: (tab) => {
        const zone = get().panelZones[tab]
        set(
          zone === 'right'
            ? { rightActiveTab: tab, rightOpen: true }
            : { bottomActiveTab: tab, bottomOpen: true },
        )
      },

      closeTabPanel: (tab) => {
        const zone = get().panelZones[tab]
        set(zone === 'right' ? { rightOpen: false } : { bottomOpen: false })
      },

      tabsInZone: (zone) => {
        const z = get().panelZones
        return (Object.keys(z) as EditorTab[]).filter((t) => z[t] === zone)
      },
    }),
    {
      name: 'fuse-editor-layout',
      version: 1,
      partialize: (s) => ({
        panelZones: s.panelZones,
        rightActiveTab: s.rightActiveTab,
        bottomActiveTab: s.bottomActiveTab,
        rightOpen: s.rightOpen,
        bottomOpen: s.bottomOpen,
        bottomHeight: s.bottomHeight,
      }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<EditorLayoutState>
        // Always enforce locked zones — guard against stale persisted state.
        const zones: Record<EditorTab, PanelZone> = {
          ...DEFAULT_ZONES,
          ...(p.panelZones ?? {}),
        }
        for (const [tab, lockedZone] of Object.entries(TAB_LOCKED_ZONES) as [
          EditorTab,
          PanelZone,
        ][]) {
          zones[tab] = lockedZone
        }
        return { ...current, ...p, panelZones: zones }
      },
    },
  ),
)
