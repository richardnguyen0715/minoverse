import { create } from 'zustand'

export type ContextPanel = 'ai' | 'backlinks' | 'related' | 'graph'

interface UIStore {
  commandPaletteOpen: boolean
  sidebarCollapsed: boolean
  activeContextPanel: ContextPanel
  openCommandPalette: () => void
  closeCommandPalette: () => void
  toggleSidebar: () => void
  setActiveContextPanel: (panel: ContextPanel) => void
}

export const useUIStore = create<UIStore>((set) => ({
  commandPaletteOpen: false,
  sidebarCollapsed: false,
  activeContextPanel: 'ai',
  openCommandPalette: () => set({ commandPaletteOpen: true }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setActiveContextPanel: (panel) => set({ activeContextPanel: panel }),
}))
