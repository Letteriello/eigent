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
 * Effect Audit Utility
 *
 * Scans React components for potential memory leaks:
 * - setTimeout without cleanup
 * - setInterval without cleanup
 * - Missing useEffect cleanup functions
 */

import * as fs from 'fs';
import * as path from 'path';

export interface AuditResult {
  filesWithTimers: string[];
  filesMissingCleanup: string[];
  totalFilesScanned: number;
  report: string;
}

/**
 * Recursively find all TypeScript/TSX files in a directory
 */
function findTypeScriptFiles(dir: string): string[] {
  const files: string[] = [];

  if (!fs.existsSync(dir)) {
    return files;
  }

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Skip node_modules, dist, .git
      if (
        entry.name !== 'node_modules' &&
        entry.name !== 'dist' &&
        entry.name !== '.git' &&
        !entry.name.startsWith('.')
      ) {
        files.push(...findTypeScriptFiles(fullPath));
      }
    } else if (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx')) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Check if a file contains setTimeout or setInterval
 */
function hasTimer(code: string): boolean {
  return code.includes('setTimeout') || code.includes('setInterval');
}

/**
 * Check if a file has proper cleanup (return () => cleanup)
 * This is a simplified check - in reality would need AST parsing
 */
function hasCleanup(code: string): boolean {
  // Look for patterns like:
  // return () => { ... clearTimeout ... }
  // return () => { ... clearInterval ... }
  const cleanupPatterns = [
    /return\s*\(\s*\)\s*=>\s*\{[^}]*clearTimeout/,
    /return\s*\(\s*\)\s*=>\s*\{[^}]*clearInterval/,
    /return\s+function\s*\(\s*\)[^{]*\{[^}]*clearTimeout/,
    /return\s+function\s*\(\s*\)[^{]*\{[^}]*clearInterval/,
  ];

  return cleanupPatterns.some((pattern) => pattern.test(code));
}

/**
 * Audit the codebase for potential memory leaks
 */
export async function auditEffectCleanup(srcDir: string): Promise<AuditResult> {
  const files = findTypeScriptFiles(srcDir);
  const filesWithTimers: string[] = [];
  const filesMissingCleanup: string[] = [];

  for (const file of files) {
    try {
      const code = fs.readFileSync(file, 'utf-8');

      if (hasTimer(code)) {
        // Normalize path to use forward slashes for cross-platform compatibility
        const normalizedPath = file.replace(/\\/g, '/');
        filesWithTimers.push(normalizedPath);

        if (!hasCleanup(code)) {
          filesMissingCleanup.push(normalizedPath);
        }
      }
    } catch {
      // Skip files that can't be read
    }
  }

  return {
    filesWithTimers,
    filesMissingCleanup,
    totalFilesScanned: files.length,
    report: generateReport({
      filesWithTimers,
      filesMissingCleanup,
      totalFilesScanned: files.length,
      report: '',
    }),
  };
}

/**
 * Generate a human-readable report
 */
export function generateReport(results: AuditResult): string {
  let report = '# Effect Cleanup Audit Report\n\n';
  report += `Total files scanned: ${results.totalFilesScanned}\n`;
  report += `Files with timers: ${results.filesWithTimers.length}\n`;
  report += `Files potentially missing cleanup: ${results.filesMissingCleanup.length}\n\n`;

  if (results.filesMissingCleanup.length > 0) {
    report += '## Files Potentially Missing Cleanup\n\n';
    for (const file of results.filesMissingCleanup) {
      report += `- ${path.relative(process.cwd(), file)}\n`;
    }
  }

  return report;
}
