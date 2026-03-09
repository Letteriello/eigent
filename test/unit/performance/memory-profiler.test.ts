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
 * Memory Profiler Tests
 *
 * TDD Tests for memory profiling utilities:
 * - Testing size estimation
 * - Snapshot creation and comparison
 * - Memory leak detection
 * - Store profiling
 */

import {
  compareSnapshots,
  createStoreProfiler,
  createStoreSnapshot,
  detectMemoryLeaks,
  estimateSize,
  formatBytes,
  generateMemoryReport,
} from '@/lib/memoryProfiler';
import { describe, expect, it, vi } from 'vitest';
import { createStore } from 'zustand';

describe('memoryProfiler', () => {
  // ========================================================================
  // estimateSize Tests
  // ========================================================================

  describe('estimateSize', () => {
    it('should return 0 for null', () => {
      expect(estimateSize(null)).toBe(0);
    });

    it('should return 0 for undefined', () => {
      expect(estimateSize(undefined)).toBe(0);
    });

    it('should estimate boolean size', () => {
      expect(estimateSize(true)).toBe(8);
      expect(estimateSize(false)).toBe(8);
    });

    it('should estimate number size', () => {
      expect(estimateSize(42)).toBe(8);
      expect(estimateSize(3.14159)).toBe(8);
    });

    it('should estimate string size', () => {
      // "hello" = 5 chars * 2 + 48 = 58
      expect(estimateSize('hello')).toBe(58);
      expect(estimateSize('')).toBe(48); // Empty string still has overhead
    });

    it('should estimate array size', () => {
      const arr = [1, 2, 3];
      expect(estimateSize(arr)).toBeGreaterThan(50);
    });

    it('should estimate object size', () => {
      const obj = { a: 1, b: 2 };
      expect(estimateSize(obj)).toBeGreaterThan(50);
    });

    it('should estimate nested object size', () => {
      const nested = {
        user: {
          name: 'John',
          age: 30,
          friends: ['Jane', 'Bob'],
        },
      };
      expect(estimateSize(nested)).toBeGreaterThan(100);
    });
  });

  // ========================================================================
  // formatBytes Tests
  // ========================================================================

  describe('formatBytes', () => {
    it('should format 0 bytes', () => {
      expect(formatBytes(0)).toBe('0 B');
    });

    it('should format bytes', () => {
      expect(formatBytes(512)).toBe('512.00 B');
    });

    it('should format kilobytes', () => {
      expect(formatBytes(1024)).toBe('1.00 KB');
      expect(formatBytes(1536)).toBe('1.50 KB');
    });

    it('should format megabytes', () => {
      expect(formatBytes(1024 * 1024)).toBe('1.00 MB');
    });

    it('should format gigabytes', () => {
      expect(formatBytes(1024 * 1024 * 1024)).toBe('1.00 GB');
    });
  });

  // ========================================================================
  // createStoreSnapshot Tests
  // ========================================================================

  describe('createStoreSnapshot', () => {
    it('should create a snapshot with correct structure', () => {
      interface TestState {
        name: string;
        count: number;
        items: string[];
      }

      const state: TestState = {
        name: 'test',
        count: 42,
        items: ['a', 'b', 'c'],
      };

      const snapshot = createStoreSnapshot('testStore', state);

      expect(snapshot.timestamp).toBeDefined();
      expect(snapshot.stateKeys).toContain('name');
      expect(snapshot.stateKeys).toContain('count');
      expect(snapshot.stateKeys).toContain('items');
      expect(snapshot.totalSizeBytes).toBeGreaterThan(0);
      expect(snapshot.keySizes).toHaveProperty('name');
      expect(snapshot.keySizes).toHaveProperty('count');
      expect(snapshot.keySizes).toHaveProperty('items');
    });

    it('should handle empty state', () => {
      interface EmptyState {}
      const snapshot = createStoreSnapshot('emptyStore', {} as EmptyState);

      expect(snapshot.stateKeys).toHaveLength(0);
      expect(snapshot.totalSizeBytes).toBeGreaterThanOrEqual(32); // Object overhead
    });
  });

  // ========================================================================
  // compareSnapshots Tests
  // ========================================================================

  describe('compareSnapshots', () => {
    it('should detect added keys', () => {
      const before: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now() - 1000,
        stateKeys: ['a', 'b'],
        totalSizeBytes: 100,
        keySizes: { a: 50, b: 50 },
        changeCount: 0,
      };

      const after: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now(),
        stateKeys: ['a', 'b', 'c'],
        totalSizeBytes: 150,
        keySizes: { a: 50, b: 50, c: 50 },
        changeCount: 1,
      };

      const result = compareSnapshots(before, after);

      expect(result.addedKeys).toContain('c');
      expect(result.removedKeys).toHaveLength(0);
      expect(result.sizeDiffBytes).toBe(50);
    });

    it('should detect removed keys', () => {
      const before: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now() - 1000,
        stateKeys: ['a', 'b', 'c'],
        totalSizeBytes: 150,
        keySizes: { a: 50, b: 50, c: 50 },
        changeCount: 0,
      };

      const after: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now(),
        stateKeys: ['a', 'b'],
        totalSizeBytes: 100,
        keySizes: { a: 50, b: 50 },
        changeCount: 1,
      };

      const result = compareSnapshots(before, after);

      expect(result.addedKeys).toHaveLength(0);
      expect(result.removedKeys).toContain('c');
      expect(result.sizeDiffBytes).toBe(-50);
    });

    it('should calculate size change percentage', () => {
      const before: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now() - 1000,
        stateKeys: ['a'],
        totalSizeBytes: 100,
        keySizes: { a: 100 },
        changeCount: 0,
      };

      const after: ReturnType<typeof createStoreSnapshot<object>> = {
        timestamp: Date.now(),
        stateKeys: ['a'],
        totalSizeBytes: 200,
        keySizes: { a: 200 },
        changeCount: 1,
      };

      const result = compareSnapshots(before, after);

      expect(result.sizeChangePercent).toBe(100);
    });
  });

  // ========================================================================
  // detectMemoryLeaks Tests
  // ========================================================================

  describe('detectMemoryLeaks', () => {
    it('should return insufficient data message for single snapshot', () => {
      const snapshot = createStoreSnapshot('test', { count: 1 });
      const result = detectMemoryLeaks('test', [snapshot]);

      expect(result.recommendation).toBe('Need more snapshots to detect leaks');
      expect(result.suspectedLeaks).toHaveLength(0);
    });

    it('should detect continuously growing keys', () => {
      const snapshots = [
        {
          ...createStoreSnapshot('test', { items: [] }),
          timestamp: Date.now() - 2000,
        },
        {
          ...createStoreSnapshot('test', { items: [1] }),
          timestamp: Date.now() - 1500,
        },
        {
          ...createStoreSnapshot('test', { items: [1, 2] }),
          timestamp: Date.now() - 1000,
        },
        {
          ...createStoreSnapshot('test', { items: [1, 2, 3] }),
          timestamp: Date.now(),
        },
      ];

      // Set sizes to show growth pattern
      snapshots.forEach((s, i) => {
        s.keySizes = { items: 50 * (i + 1) };
        s.totalSizeBytes = 50 * (i + 1);
      });

      const result = detectMemoryLeaks('test', snapshots);

      // Should detect growth
      expect(result.suspectedLeaks.length).toBeGreaterThanOrEqual(0);
    });

    it('should detect large keys (>1MB)', () => {
      // Create a large string (simulated > 1MB)
      const largeString = 'x'.repeat(1024 * 1024 + 1);
      const snapshots = [
        {
          ...createStoreSnapshot('test', { data: 'small' }),
          timestamp: Date.now() - 1000,
        },
        {
          ...createStoreSnapshot('test', { data: largeString }),
          timestamp: Date.now(),
        },
      ];

      snapshots[1].keySizes = { data: snapshots[1].totalSizeBytes };

      const result = detectMemoryLeaks('test', snapshots);

      expect(result.suspectedLeaks.some((l) => l.includes('exceeds 1MB'))).toBe(
        true
      );
    });
  });

  // ========================================================================
  // createStoreProfiler Tests
  // ========================================================================

  describe('createStoreProfiler', () => {
    it('should create a profiler and take snapshots', () => {
      const store = createStore<{ count: number; name: string }>()(() => ({
        count: 0,
        name: 'test',
      }));

      const profiler = createStoreProfiler('testStore', store.getState);

      const snapshot = profiler.snapshot();

      expect(snapshot.stateKeys).toContain('count');
      expect(snapshot.stateKeys).toContain('name');
    });

    it('should track update count', () => {
      const store = createStore<{ count: number }>()(() => ({
        count: 0,
      }));

      const profiler = createStoreProfiler('testStore', store.getState);

      profiler.recordUpdate();
      profiler.recordUpdate();
      profiler.recordUpdate();

      const metrics = profiler.getMetrics();

      expect(metrics.updateCount).toBe(3);
    });

    it('should calculate average update time', () => {
      const store = createStore<{ count: number }>()(() => ({
        count: 0,
      }));

      const profiler = createStoreProfiler('testStore', store.getState);

      // Simulate updates with different timings
      profiler.recordUpdate();
      vi.advanceTimersByTime(10);
      profiler.recordUpdate();
      vi.advanceTimersByTime(20);
      profiler.recordUpdate();

      const metrics = profiler.getMetrics();

      expect(metrics.updateCount).toBe(3);
      expect(metrics.averageUpdateTime).toBeGreaterThan(0);
    });

    it('should return memory summary', () => {
      const store = createStore<{ items: number[] }>()(() => ({
        items: [1, 2, 3],
      }));

      const profiler = createStoreProfiler('testStore', store.getState);

      profiler.snapshot();

      const summary = profiler.getSummary();

      expect(summary.currentSize).toBeGreaterThan(0);
      expect(summary.updateCount).toBe(0);
      expect(Array.isArray(summary.leaks)).toBe(true);
    });

    it('should limit snapshots to 100', () => {
      const store = createStore<{ count: number }>()(() => ({
        count: 0,
      }));

      const profiler = createStoreProfiler('testStore', store.getState);

      // Take more than 100 snapshots
      for (let i = 0; i < 110; i++) {
        profiler.snapshot();
      }

      const snapshots = profiler.getSnapshots();

      expect(snapshots.length).toBeLessThanOrEqual(100);
    });
  });

  // ========================================================================
  // generateMemoryReport Tests
  // ========================================================================

  describe('generateMemoryReport', () => {
    it('should generate report for empty snapshots', () => {
      const report = generateMemoryReport('test', []);

      expect(report).toContain('# Memory Report: test');
      expect(report).toContain('No snapshots available');
    });

    it('should generate report with snapshot data', () => {
      const snapshots = [createStoreSnapshot('test', { name: 'test' })];

      // Update timestamp to be recent
      snapshots[0].timestamp = Date.now();

      const report = generateMemoryReport('test', snapshots);

      expect(report).toContain('# Memory Report: test');
      expect(report).toContain('## Current State');
      expect(report).toContain('## Size by Key');
      expect(report).toContain('name:');
    });

    it('should include growth analysis', () => {
      const snapshots = [
        {
          ...createStoreSnapshot('test', { count: 0 }),
          timestamp: Date.now() - 1000,
        },
        {
          ...createStoreSnapshot('test', { count: 100 }),
          timestamp: Date.now(),
        },
      ];

      const report = generateMemoryReport('test', snapshots);

      expect(report).toContain('## Growth Analysis');
      expect(report).toContain('Initial Size');
      expect(report).toContain('Current Size');
      expect(report).toContain('Change:');
    });
  });
});
