import { create } from 'zustand'
import type { Resource } from '@/lib/types'

interface KnowledgeStore {
  searchQuery: string
  searchResults: Resource[]
  recentResources: Resource[]
  setSearchQuery: (q: string) => void
  setSearchResults: (results: Resource[]) => void
  addRecentResource: (resource: Resource) => void
}

export const useKnowledgeStore = create<KnowledgeStore>((set) => ({
  searchQuery: '',
  searchResults: [],
  recentResources: [],
  setSearchQuery: (q) => set({ searchQuery: q }),
  setSearchResults: (results) => set({ searchResults: results }),
  addRecentResource: (resource) =>
    set((s) => ({
      recentResources: [resource, ...s.recentResources.filter((r) => r.id !== resource.id)].slice(0, 5),
    })),
}))
