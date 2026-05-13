// Zustand store — global app state

import { create } from "zustand"

interface AppState {
  // Auth
  apiUrl: string
  apiKey?: string
  setApiUrl: (url: string) => void
  setApiKey: (key: string) => void

  // Recent activity
  recentItems: RecentItem[]
  addRecentItem: (item: RecentItem) => void
  clearRecent: () => void
}

export interface RecentItem {
  id: string
  title?: string
  url: string
  source_type: string
  timestamp: number
}

export const useAppStore = create<AppState>((set) => ({
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
  apiKey: undefined,

  setApiUrl: (url) => set({ apiUrl: url }),
  setApiKey: (key) => set({ apiKey: key }),

  recentItems: [],
  addRecentItem: (item) =>
    set((state) => ({
      recentItems: [item, ...state.recentItems.filter((i) => i.id !== item.id)].slice(0, 50),
    })),
  clearRecent: () => set({ recentItems: [] }),
}))
