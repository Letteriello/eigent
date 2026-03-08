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
 * TDD Test: Effect Audit Script
 *
 * This test verifies the audit script can scan the codebase for:
 * 1. Files with setTimeout/setInterval in useEffect
 * 2. Detection of missing cleanup functions
 * 3. Reporting of files with potential memory leaks
 */

import * as path from 'path';
import { describe, expect, it } from 'vitest';

describe('Effect Audit Script', () => {
  const SRC_DIR = path.join(process.cwd(), 'src');

  it('should find files with setTimeout in useEffect', async () => {
    // Import the audit utility - this will fail until we implement it
    const { auditEffectCleanup } = await import('../../src/lib/effectAudit');

    const results = await auditEffectCleanup(SRC_DIR);

    // Should find files with timers
    expect(results.filesWithTimers.length).toBeGreaterThan(0);
  });

  it('should identify files missing cleanup', async () => {
    const { auditEffectCleanup } = await import('../../src/lib/effectAudit');

    const results = await auditEffectCleanup(SRC_DIR);

    // Should identify files that may have memory leaks
    expect(results.filesMissingCleanup).toBeDefined();
    expect(Array.isArray(results.filesMissingCleanup)).toBe(true);
  });

  it('should generate audit report', async () => {
    const { auditEffectCleanup, generateReport } =
      await import('../../src/lib/effectAudit');

    const results = await auditEffectCleanup(SRC_DIR);
    const report = generateReport(results);

    expect(report).toBeDefined();
    expect(typeof report).toBe('string');
    expect(report.length).toBeGreaterThan(0);
  });

  it('should detect MCP.tsx polling interval pattern', async () => {
    const { auditEffectCleanup } = await import('../../src/lib/effectAudit');

    const results = await auditEffectCleanup(SRC_DIR);

    // MCP.tsx is known to have polling - should be in results
    // Use case-insensitive search
    const mcpFile = results.filesWithTimers.find((f: string) =>
      f.toLowerCase().includes('mcp.tsx')
    );
    expect(mcpFile).toBeDefined();
  });
});
