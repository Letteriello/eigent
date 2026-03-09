// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import { create } from 'zustand';
import { shallow } from 'zustand/shallow';

export type MemoryType = 'fact' | 'preference' | 'context' | 'learned';

export type ImportanceSource = 'auto' | 'manual';

export interface Memory {
  id: string;
  content: string;
  memory_type: MemoryType;
  metadata: Record<string, unknown>;
  agent_id: string | null;
  session_id: string | null;
  importance: number;
  importance_source?: ImportanceSource;
  last_recalled_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MemorySearchResult {
  memories: Memory[];
  total: number;
  query: string;
}

export type SummaryQuality = 'excellent' | 'good' | 'partial';

export interface MemorySummary {
  id: string;
  memoryId: string;
  content: string;
  sourceCount: number;
  generatedAt: string;
  quality: SummaryQuality;
}

export interface MemoryStats {
  total_memories: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
}

interface MemoryState {
  memories: Memory[];
  searchResults: Memory[];
  stats: MemoryStats | null;
  isLoading: boolean;
  error: string | null;
  lastSearchQuery: string;

  // Summary state
  summaries: Record<string, MemorySummary>;
  summarizationStatus: 'idle' | 'summarizing' | 'error';

  // Actions
  fetchMemories: () => Promise<void>;
  createMemory: (
    content: string,
    memoryType: MemoryType,
    metadata?: Record<string, unknown>,
    agentId?: string,
    sessionId?: string
  ) => Promise<Memory | null>;
  updateMemory: (
    id: string,
    content: string,
    memoryType: MemoryType,
    metadata?: Record<string, unknown>
  ) => Promise<Memory | null>;
  deleteMemory: (id: string) => Promise<boolean>;
  searchMemories: (
    query: string,
    memoryType?: MemoryType,
    agentId?: string,
    topK?: number
  ) => Promise<MemorySearchResult | null>;
  fetchStats: () => Promise<void>;
  clearError: () => void;

  // Summary actions
  summarizeMemory: (memoryId: string) => Promise<MemorySummary | null>;
  getSummary: (memoryId: string) => MemorySummary | null;

  // Backup actions
  exportMemories: () => Promise<string | null>;
  importMemories: (jsonData: string) => Promise<number>;
}

const API_BASE = '/api/memory';

export const useMemoryStore = create<MemoryState>()(
  (set, get) => ({
      memories: [],
      searchResults: [],
      stats: null,
      isLoading: false,
      error: null,
      lastSearchQuery: '',

      // Summary state
      summaries: {},
      summarizationStatus: 'idle',

      fetchMemories: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(API_BASE, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          });

          if (!response.ok) {
            throw new Error(`Failed to fetch memories: ${response.statusText}`);
          }

          const memories = (await response.json()) as Memory[];
          set({ memories, isLoading: false });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to fetch memories:', error);
        }
      },

      createMemory: async (
        content: string,
        memoryType: MemoryType,
        metadata = {},
        agentId?: string,
        sessionId?: string
      ) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(API_BASE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content,
              memory_type: memoryType,
              metadata,
              agent_id: agentId ?? null,
              session_id: sessionId ?? null,
            }),
          });

          if (!response.ok) {
            throw new Error(`Failed to create memory: ${response.statusText}`);
          }

          const memory = (await response.json()) as Memory;

          // Update local state
          set((state) => ({
            memories: [memory, ...state.memories],
            isLoading: false,
          }));

          return memory;
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to create memory:', error);
          return null;
        }
      },

      updateMemory: async (
        id: string,
        content: string,
        memoryType: MemoryType,
        metadata
      ) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content,
              memory_type: memoryType,
              metadata,
            }),
          });

          if (!response.ok) {
            throw new Error(`Failed to update memory: ${response.statusText}`);
          }

          const memory = (await response.json()) as Memory;

          // Update local state
          set((state) => ({
            memories: state.memories.map((m) => (m.id === id ? memory : m)),
            isLoading: false,
          }));

          return memory;
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to update memory:', error);
          return null;
        }
      },

      deleteMemory: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
          });

          if (!response.ok) {
            throw new Error(`Failed to delete memory: ${response.statusText}`);
          }

          // Update local state
          set((state) => ({
            memories: state.memories.filter((m) => m.id !== id),
            isLoading: false,
          }));

          return true;
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to delete memory:', error);
          return false;
        }
      },

      searchMemories: async (
        query: string,
        memoryType?: MemoryType,
        agentId?: string,
        topK = 10
      ) => {
        set({ isLoading: true, error: null, lastSearchQuery: query });
        try {
          const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              memory_type: memoryType ?? null,
              agent_id: agentId ?? null,
              top_k: topK,
              similarity_threshold: 0.3,
            }),
          });

          if (!response.ok) {
            throw new Error(
              `Failed to search memories: ${response.statusText}`
            );
          }

          const result = (await response.json()) as MemorySearchResult;

          set({
            searchResults: result.memories,
            isLoading: false,
          });

          return result;
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to search memories:', error);
          return null;
        }
      },

      fetchStats: async () => {
        try {
          const response = await fetch(`${API_BASE}/stats`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          });

          if (!response.ok) {
            throw new Error(`Failed to fetch stats: ${response.statusText}`);
          }

          const stats = (await response.json()) as MemoryStats;
          set({ stats });
        } catch (error) {
          console.error('[MemoryStore] Failed to fetch stats:', error);
        }
      },

      clearError: () => {
        set({ error: null });
      },

      summarizeMemory: async (memoryId: string) => {
        set({ summarizationStatus: 'summarizing', error: null });
        try {
          const response = await fetch(`${API_BASE}/${memoryId}/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });

          if (!response.ok) {
            throw new Error(
              `Failed to summarize memory: ${response.statusText}`
            );
          }

          const summary = (await response.json()) as MemorySummary;

          // Update local state
          set((state) => ({
            summaries: {
              ...state.summaries,
              [memoryId]: summary,
            },
            summarizationStatus: 'idle',
          }));

          return summary;
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, summarizationStatus: 'error' });
          console.error('[MemoryStore] Failed to summarize memory:', error);
          return null;
        }
      },

      getSummary: (memoryId: string): MemorySummary | null => {
        const state = get();
        return state.summaries[memoryId] ?? null;
      },

      exportMemories: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });

          if (!response.ok) {
            throw new Error(`Failed to export memories: ${response.statusText}`);
          }

          const data = await response.json();
          set({ isLoading: false });

          // Create and download JSON file
          const jsonStr = JSON.stringify(data, null, 2);
          const blob = new Blob([jsonStr], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `eigent-memories-${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);

          return jsonStr;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to export memories:', error);
          return null;
        }
      },

      importMemories: async (jsonData: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: jsonData,
          });

          if (!response.ok) {
            throw new Error(`Failed to import memories: ${response.statusText}`);
          }

          const result = await response.json();
          set({ isLoading: false });

          // Refresh memories and stats after import
          await get().fetchMemories();
          await get().fetchStats();

          return result.imported || 0;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          set({ error: message, isLoading: false });
          console.error('[MemoryStore] Failed to import memories:', error);
          return 0;
        }
      },
    })
);

// ========= OPTIMIZED SELECTORS (prevent unnecessary re-renders) =========

// Selector for memories list with shallow equality
export const useMemories = () =>
  useMemoryStore((state) => state.memories, shallow);

// Selector for search results with shallow equality
export const useSearchResults = () =>
  useMemoryStore((state) => state.searchResults, shallow);

// Selector for loading and error state
export const useMemoryStatus = () =>
  useMemoryStore(
    (state) => ({
      isLoading: state.isLoading,
      error: state.error,
      lastSearchQuery: state.lastSearchQuery,
    }),
    shallow
  );

// Selector for memory stats
export const useMemoryStats = () =>
  useMemoryStore((state) => state.stats, shallow);

// Selector for summarization status
export const useSummarizationStatus = () =>
  useMemoryStore((state) => state.summarizationStatus, shallow);

// Selector for a specific memory summary
export const useMemorySummary = (memoryId: string) =>
  useMemoryStore((state) => state.summaries[memoryId] ?? null, shallow);
