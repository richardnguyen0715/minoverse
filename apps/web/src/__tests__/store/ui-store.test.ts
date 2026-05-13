import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from '@/store/ui-store'

describe('UIStore', () => {
  beforeEach(() => {
    useUIStore.setState({
      commandPaletteOpen: false,
      sidebarCollapsed: false,
      activeContextPanel: 'ai',
    })
  })

  it('opens command palette', () => {
    useUIStore.getState().openCommandPalette()
    expect(useUIStore.getState().commandPaletteOpen).toBe(true)
  })

  it('closes command palette', () => {
    useUIStore.setState({ commandPaletteOpen: true })
    useUIStore.getState().closeCommandPalette()
    expect(useUIStore.getState().commandPaletteOpen).toBe(false)
  })

  it('toggles sidebar', () => {
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(true)
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(false)
  })

  it('sets active context panel', () => {
    useUIStore.getState().setActiveContextPanel('graph')
    expect(useUIStore.getState().activeContextPanel).toBe('graph')
  })
})
