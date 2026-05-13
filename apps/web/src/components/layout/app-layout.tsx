'use client'
import { useUIStore } from '@/store/ui-store'
import { Sidebar } from './sidebar'
import { CommandPalette } from '../command-palette'
import { useEffect } from 'react'

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { commandPaletteOpen, openCommandPalette, closeCommandPalette, sidebarCollapsed } = useUIStore()

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        openCommandPalette()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [openCommandPalette])

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar collapsed={sidebarCollapsed} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="flex items-center justify-between px-4 py-2 border-b border-border/50 bg-background/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-primary">⬡ minoverse</span>
          </div>
          <button
            onClick={openCommandPalette}
            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground px-3 py-1.5 border border-border/50 rounded-md hover:bg-accent transition-colors"
          >
            <span>Search knowledge base...</span>
            <kbd className="px-1 py-0.5 bg-muted rounded text-[10px]">⌘K</kbd>
          </button>
        </header>
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
      {commandPaletteOpen && <CommandPalette onClose={closeCommandPalette} />}
    </div>
  )
}
