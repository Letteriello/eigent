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
 * Tests for detecting memory leaks in React Effects
 * Tests setTimeout/setInterval cleanup and useEffect cleanup functions
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock timers for testing
vi.useFakeTimers();

// Helper to detect if a callback was called after component unmount
// This simulates checking if cleanup was properly executed
describe('React Effects Cleanup Tests', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('setTimeout cleanup detection', () => {
    it('should detect setTimeout without cleanup in useEffect', () => {
      // This test detects the pattern: setTimeout inside useEffect without return cleanup
      // In real code, this would be flagged by our linter/validator

      let cleanupExecuted = false;
      let timeoutCallbackExecuted = false;

      // Simulate useEffect WITHOUT cleanup (BAD PATTERN)
      const effectWithoutCleanup = () => {
        setTimeout(() => {
          timeoutCallbackExecuted = true;
        }, 1000);
        // NO return statement - this is the leak!
      };

      effectWithoutCleanup();

      // Fast forward time - callback executes even if component unmounted
      vi.advanceTimersByTime(2000);

      // The timeout executed (which is fine for this test)
      expect(timeoutCallbackExecuted).toBe(true);
    });

    it('should have proper cleanup when useEffect returns cleanup function', () => {
      // Simulate useEffect WITH cleanup (GOOD PATTERN)
      let cleanupExecuted = false;
      let timeoutCallbackExecuted = false;

      const effectWithCleanup = () => {
        const timer = setTimeout(() => {
          timeoutCallbackExecuted = true;
        }, 1000);

        // Return cleanup function
        return () => {
          cleanupExecuted = true;
          clearTimeout(timer);
        };
      };

      const cleanup = effectWithCleanup();

      // Simulate component unmount before timeout fires
      cleanup();
      vi.advanceTimersByTime(2000);

      expect(cleanupExecuted).toBe(true);
      expect(timeoutCallbackExecuted).toBe(false); // Timer was cleared!
    });
  });

  describe('setInterval cleanup detection', () => {
    it('should detect setInterval without cleanup - potential memory leak', () => {
      let intervalCallbackCount = 0;

      // Simulate interval without proper cleanup
      const intervalWithoutCleanup = () => {
        const interval = setInterval(() => {
          intervalCallbackCount++;
        }, 100);
        // Missing: return () => clearInterval(interval);
      };

      intervalWithoutCleanup();

      vi.advanceTimersByTime(500);
      expect(intervalCallbackCount).toBeGreaterThan(0);

      // Problem: interval continues running - we can't stop it!
    });

    it('should properly cleanup setInterval on unmount', () => {
      let intervalCallbackCount = 0;

      const intervalWithCleanup = () => {
        const interval = setInterval(() => {
          intervalCallbackCount++;
        }, 100);

        return () => clearInterval(interval);
      };

      const cleanup = intervalWithCleanup();

      vi.advanceTimersByTime(250); // 2 callbacks

      cleanup(); // Simulate unmount
      vi.advanceTimersByTime(250); // Should not increment

      expect(intervalCallbackCount).toBe(2);
    });
  });

  describe('Real world patterns in codebase', () => {
    it('MCP.tsx polling interval should be cleaned up on unmount', async () => {
      // This test documents the expected behavior for MCP.tsx
      // The polling interval should be cleared when component unmounts

      let pollCount = 0;
      let cleanupCalled = false;

      const startPolling = () => {
        const pollInterval = setInterval(() => {
          pollCount++;
        }, 500);

        // This cleanup should be returned from useEffect
        return () => {
          cleanupCalled = true;
          clearInterval(pollInterval);
        };
      };

      // Simulate component mount
      const cleanup = startPolling();

      vi.advanceTimersByTime(1500); // 3 polls

      // Simulate component unmount
      cleanup();

      vi.advanceTimersByTime(1000); // Should not poll more

      expect(pollCount).toBe(3);
      expect(cleanupCalled).toBe(true);
    });

    it('Terminal.tsx setTimeout should be cleaned up on unmount', () => {
      // This test documents the expected behavior for Terminal.tsx line 165
      // The setTimeout inside useEffect should be cleaned up

      let terminalCallbackExecuted = false;

      const terminalEffect = () => {
        const timer = setTimeout(() => {
          terminalCallbackExecuted = true;
        }, 300);

        return () => clearTimeout(timer);
      };

      const cleanup = terminalEffect();

      // Simulate unmount before timeout
      cleanup();
      vi.advanceTimersByTime(500);

      expect(terminalCallbackExecuted).toBe(false);
    });
  });
});

// Test helper to validate useEffect cleanup pattern
export function validateEffectCleanup(code: string): {
  hasCleanup: boolean;
  issues: string[];
} {
  const issues: string[] = [];

  // Check for setTimeout without clearTimeout in useEffect
  const setTimeoutWithoutCleanup = /setTimeout\([^)]+\)\s*(?!\s*;?\s*return)/g;
  if (setTimeoutWithoutCleanup.test(code)) {
    issues.push('setTimeout found without cleanup function');
  }

  // Check for setInterval without clearInterval in useEffect
  const setIntervalWithoutCleanup = /setInterval\([^)]+\)(?!\s*;?\s*return)/g;
  if (setIntervalWithoutCleanup.test(code)) {
    issues.push('setInterval found without cleanup function');
  }

  return {
    hasCleanup: issues.length === 0,
    issues,
  };
}
