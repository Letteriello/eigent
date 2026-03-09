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

/**
 * Memory Profiler Utilities for Zustand Stores
 *
 * This module provides memory profiling capabilities for Zustand stores:
 * - Track state size and changes
 * - Detect potential memory leaks
 * - Monitor selector performance
 * - Generate memory reports
 */

/**
 * Memory snapshot of a Zustand store state
 */
export interface StoreMemorySnapshot {
  timestamp: number;
  stateKeys: string[];
  totalSizeBytes: number;
  keySizes: Record<string, number>;
  changeCount: number;
}

/**
 * Memory leak detection result
 */
export interface MemoryLeakResult {
  storeName: string;
  suspectedLeaks: string[];
  recommendation: string;
}

/**
 * Performance metrics for store operations
 */
export interface StoreMetrics {
  storeName: string;
  updateCount: number;
  lastUpdateTime: number;
  averageUpdateTime: number;
  subscriberCount: number;
}

/**
 * Calculate the approximate size of a value in bytes
 * This is an estimation - actual memory usage may vary
 */
export function estimateSize(value: unknown): number {
  if (value === null || value === undefined) {
    return 0;
  }

  if (typeof value === 'boolean' || typeof value === 'number') {
    return 8;
  }

  if (typeof value === 'string') {
    return value.length * 2 + 48; // String overhead
  }

  if (Array.isArray(value)) {
    return value.reduce((acc, item) => acc + estimateSize(item), 0) + 32;
  }

  if (typeof value === 'object') {
    let size = 32; // Object overhead
    for (const key of Object.keys(value as object)) {
      size += key.length * 2 + 32;
      size += estimateSize((value as Record<string, unknown>)[key]);
    }
    return size;
  }

  return 16;
}

/**
 * Create a memory snapshot of a Zustand store
 */
export function createStoreSnapshot<T extends object>(
  storeName: string,
  state: T
): StoreMemorySnapshot {
  const keySizes: Record<string, number> = {};
  let totalSize = 0;

  for (const key of Object.keys(state)) {
    const size = estimateSize((state as Record<string, unknown>)[key]);
    keySizes[key] = size;
    totalSize += size;
  }

  return {
    timestamp: Date.now(),
    stateKeys: Object.keys(state),
    totalSizeBytes: totalSize,
    keySizes,
    changeCount: 0,
  };
}

/**
 * Compare two store snapshots and return changes
 */
export function compareSnapshots(
  before: StoreMemorySnapshot,
  after: StoreMemorySnapshot
): {
  addedKeys: string[];
  removedKeys: string[];
  sizeDiffBytes: number;
  sizeChangePercent: number;
} {
  const beforeKeys = new Set(before.stateKeys);
  const afterKeys = new Set(after.stateKeys);

  const addedKeys = after.stateKeys.filter((k) => !beforeKeys.has(k));
  const removedKeys = before.stateKeys.filter((k) => !afterKeys.has(k));
  const sizeDiff = after.totalSizeBytes - before.totalSizeBytes;
  const sizeChangePercent =
    before.totalSizeBytes > 0 ? (sizeDiff / before.totalSizeBytes) * 100 : 0;

  return {
    addedKeys,
    removedKeys,
    sizeDiffBytes: sizeDiff,
    sizeChangePercent,
  };
}

/**
 * Detect potential memory leaks in Zustand stores
 */
export function detectMemoryLeaks<T extends object>(
  storeName: string,
  snapshots: StoreMemorySnapshot[]
): MemoryLeakResult {
  if (snapshots.length < 2) {
    return {
      storeName,
      suspectedLeaks: [],
      recommendation: 'Need more snapshots to detect leaks',
    };
  }

  const suspectedLeaks: string[] = [];
  const recentSnapshots = snapshots.slice(-10); // Look at last 10

  // Check for continuous growth
  let growingKeys = 0;
  for (const key of recentSnapshots[0].stateKeys) {
    const sizes = recentSnapshots.map((s) => s.keySizes[key] || 0);
    const isGrowing = sizes.every((size, i) => i === 0 || size >= sizes[i - 1]);

    if (isGrowing && sizes[sizes.length - 1] > sizes[0] * 1.5) {
      growingKeys++;
      suspectedLeaks.push(`${key} is continuously growing`);
    }
  }

  // Check for unbounded growth (array/object accumulation)
  const latestSnapshot = recentSnapshots[recentSnapshots.length - 1];
  for (const [key, size] of Object.entries(latestSnapshot.keySizes)) {
    if (size > 1024 * 1024) {
      // > 1MB
      suspectedLeaks.push(
        `${key} exceeds 1MB (${(size / 1024 / 1024).toFixed(2)}MB)`
      );
    }
  }

  const recommendation =
    suspectedLeaks.length > 0
      ? `Consider implementing cleanup for: ${suspectedLeaks[0]}`
      : 'No obvious memory leaks detected';

  return {
    storeName,
    suspectedLeaks,
    recommendation,
  };
}

/**
 * Create a store profiler for tracking memory usage over time
 */
export function createStoreProfiler<T extends object>(
  storeName: string,
  getState: () => T
) {
  const snapshots: StoreMemorySnapshot[] = [];
  let updateCount = 0;
  let lastUpdateTime = Date.now();
  const updateTimes: number[] = [];

  return {
    /**
     * Take a snapshot of current store state
     */
    snapshot(): StoreMemorySnapshot {
      const state = getState();
      const snapshot = createStoreSnapshot(storeName, state);
      snapshot.changeCount = updateCount;
      snapshots.push(snapshot);

      // Keep only last 100 snapshots
      if (snapshots.length > 100) {
        snapshots.shift();
      }

      return snapshot;
    },

    /**
     * Record an update operation
     */
    recordUpdate() {
      const now = Date.now();
      const updateTime = now - lastUpdateTime;
      updateTimes.push(updateTime);
      lastUpdateTime = now;
      updateCount++;

      // Keep only last 100 update times
      if (updateTimes.length > 100) {
        updateTimes.shift();
      }
    },

    /**
     * Get performance metrics
     */
    getMetrics(): StoreMetrics {
      const avgUpdateTime =
        updateTimes.length > 0
          ? updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length
          : 0;

      return {
        storeName,
        updateCount,
        lastUpdateTime,
        averageUpdateTime: avgUpdateTime,
        subscriberCount: 0, // Can't reliably get this from zustand
      };
    },

    /**
     * Get all snapshots
     */
    getSnapshots(): StoreMemorySnapshot[] {
      return [...snapshots];
    },

    /**
     * Check for memory leaks
     */
    checkLeaks(): MemoryLeakResult {
      return detectMemoryLeaks(storeName, snapshots);
    },

    /**
     * Get memory summary
     */
    getSummary(): {
      currentSize: number;
      sizeChange: number;
      updateCount: number;
      leaks: string[];
    } {
      if (snapshots.length === 0) {
        return {
          currentSize: 0,
          sizeChange: 0,
          updateCount: 0,
          leaks: [],
        };
      }

      const latest = snapshots[snapshots.length - 1];
      const oldest = snapshots[0];
      const leaks = detectMemoryLeaks(storeName, snapshots);

      return {
        currentSize: latest.totalSizeBytes,
        sizeChange: latest.totalSizeBytes - oldest.totalSizeBytes,
        updateCount,
        leaks: leaks.suspectedLeaks,
      };
    },

    /**
     * Cleanup and release all stored data
     * Call this when the profiler is no longer needed to prevent memory leaks
     */
    dispose() {
      snapshots.length = 0;
      updateTimes.length = 0;
      updateCount = 0;
      lastUpdateTime = Date.now();
    },
  };
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * Generate a memory report for a store
 */
export function generateMemoryReport(
  storeName: string,
  snapshots: StoreMemorySnapshot[]
): string {
  let report = `# Memory Report: ${storeName}\n\n`;

  if (snapshots.length === 0) {
    report += 'No snapshots available.\n';
    return report;
  }

  const latest = snapshots[snapshots.length - 1];
  const oldest = snapshots[0];

  report += `## Current State\n\n`;
  report += `- Total Size: ${formatBytes(latest.totalSizeBytes)}\n`;
  report += `- State Keys: ${latest.stateKeys.length}\n`;
  report += `- Updates: ${latest.changeCount}\n\n`;

  report += `## Size by Key\n\n`;
  for (const [key, size] of Object.entries(latest.keySizes)) {
    report += `- ${key}: ${formatBytes(size)}\n`;
  }

  report += `\n## Growth Analysis\n\n`;
  report += `- Initial Size: ${formatBytes(oldest.totalSizeBytes)}\n`;
  report += `- Current Size: ${formatBytes(latest.totalSizeBytes)}\n`;
  report += `- Change: ${formatBytes(latest.totalSizeBytes - oldest.totalSizeBytes)} `;
  report += `(${
    oldest.totalSizeBytes > 0
      ? (
          ((latest.totalSizeBytes - oldest.totalSizeBytes) /
            oldest.totalSizeBytes) *
          100
        ).toFixed(1)
      : 0
  }%)\n`;

  const leaks = detectMemoryLeaks(storeName, snapshots);
  if (leaks.suspectedLeaks.length > 0) {
    report += `\n## Potential Memory Leaks\n\n`;
    for (const leak of leaks.suspectedLeaks) {
      report += `- ${leak}\n`;
    }
  }

  return report;
}

// ============================================================================
// React Integration Hooks
// ============================================================================

/**
 * Hook to monitor store memory usage
 * Use in development only - may impact performance
 */
export interface UseStoreMemoryOptions {
  storeName: string;
  getState: () => unknown;
  enabled?: boolean;
}

/**
 * Create a memory monitoring hook for a store
 * This is a factory function - use it to create store-specific hooks
 */
export function createMemoryMonitorHook<T extends object>(
  storeName: string,
  useStore: (
    selector?: (state: T) => unknown,
    options?: { shallow?: boolean }
  ) => unknown
) {
  return function useStoreMemory() {
    const state = useStore((s) => s as T);
    const stateRecord = state as Record<string, unknown>;

    return {
      storeName,
      stateSize: estimateSize(state),
      keys: Object.keys(stateRecord),
      keySizes: Object.fromEntries(
        Object.keys(stateRecord).map((k) => [
          k,
          estimateSize(stateRecord[k]),
        ])
      ),
    };
  };
}
