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
import { persist } from 'zustand/middleware';

export type MemoryType = 'fact' | 'preference' | 'context' | 'learned';

export interface Memory {
  id: string;
  content: string;
  memory_type: MemoryType;
  metadata: Record<string, unknown>;
  agent_id: string | null;
  session_id: string | null;
  importance: number;
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
}

const API_BASE = '/api/memory';

// Maximum memories to persist in localStorage to prevent unbounded growth
const MAX_PERSISTED_MEMORIES = 1000;
// Maximum summaries to persist in localStorage
const MAX_PERSISTED_SUMMARIES = 500;

/**
 * Trim memories array to maximum size, keeping most recent entries
 */
function trimMemories(memories: Memory[]): Memory[] {
  if (memories.length > MAX_PERSISTED_MEMORIES) {
    console.warn(
      `[MemoryStore] Trimming memories from ${memories.length} to ${MAX_PERSISTED_MEMORIES}`
    );
    return memories.slice(0, MAX_PERSISTED_MEMORIES);
  }
  return memories;
}

/**
 * Trim summaries object to maximum size, keeping most recent entries
 */
function trimSummaries(
  summaries: Record<string, MemorySummary>
): Record<string, MemorySummary> {
  const entries = Object.entries(summaries);
  if (entries.length > MAX_PERSISTED_SUMMARIES) {
    console.warn(
      `[MemoryStore] Trimming summaries from ${entries.length} to ${MAX_PERSISTED_SUMMARIES}`
    );
    // Sort by generatedAt (most recent first) and keep top N
    const sorted = entries.sort((a, b) => {
      const dateA = new Date(a[1].generatedAt).getTime();
      const dateB = new Date(b[1].generatedAt).getTime();
      return dateB - dateA;
    });
    return Object.fromEntries(sorted.slice(0, MAX_PERSISTED_SUMMARIES));
  }
  return summaries;
}

export const useMemoryStore = create<MemoryState>()(
  persist(
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

          // Update local state with trim to prevent unbounded growth
          set((state) => ({
            memories: trimMemories([memory, ...state.memories]),
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

          // Update local state with trim to prevent unbounded growth
          set((state) => ({
            summaries: trimSummaries({
              ...state.summaries,
              [memoryId]: summary,
            }),
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
    }),
    {
      name: 'memory-storage',
      partialize: (state) => ({
        memories: trimMemories(state.memories),
        summaries: trimSummaries(state.summaries),
      }),
    }
  )
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
