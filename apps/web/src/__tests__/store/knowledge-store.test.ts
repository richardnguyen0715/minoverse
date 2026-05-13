import { describe, it, expect, beforeEach } from 'vitest'
import { useKnowledgeStore } from '@/store/knowledge-store'
import type { Resource } from '@/lib/types'

const mockResource: Resource = {
  id: 'abc-123',
  vault_file_id: null,
  resource_type: 'paper',
  title: 'Test Paper',
  url: null,
  author: 'Test Author',
  language: null,
  extra_metadata: null,
  is_favorite: false,
  is_archived: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('KnowledgeStore', () => {
  beforeEach(() => {
    useKnowledgeStore.setState({ searchQuery: '', searchResults: [], recentResources: [] })
  })

  it('sets search query', () => {
    useKnowledgeStore.getState().setSearchQuery('transformers')
    expect(useKnowledgeStore.getState().searchQuery).toBe('transformers')
  })

  it('adds recent resource to front of list', () => {
    useKnowledgeStore.getState().addRecentResource(mockResource)
    expect(useKnowledgeStore.getState().recentResources[0].id).toBe('abc-123')
  })

  it('deduplicates recent resources', () => {
    useKnowledgeStore.getState().addRecentResource(mockResource)
    useKnowledgeStore.getState().addRecentResource(mockResource)
    expect(useKnowledgeStore.getState().recentResources).toHaveLength(1)
  })

  it('keeps max 5 recent resources', () => {
    for (let i = 0; i < 7; i++) {
      useKnowledgeStore.getState().addRecentResource({ ...mockResource, id: `id-${i}` })
    }
    expect(useKnowledgeStore.getState().recentResources).toHaveLength(5)
  })
})
