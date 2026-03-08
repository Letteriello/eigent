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

import react from '@vitejs/plugin-react';
import { existsSync, readFileSync, rmSync } from 'node:fs';
import path from 'node:path';
import { defineConfig, loadEnv } from 'vite';
import electron from 'vite-plugin-electron/simple';
import pkg from './package.json';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // PERFORMANCE: Only clean dist-electron when explicitly needed
  // This was causing slow dev server startup on every rebuild
  const shouldClean = !existsSync('dist-electron/main/index.js');
  if (shouldClean) {
    try {
      rmSync('dist-electron', { recursive: true, force: true });
    } catch {
      // Ignore if doesn't exist
    }
  }

  const isServe = command === 'serve';
  const isBuild = command === 'build';
  const sourcemap = isServe || !!process.env.VSCODE_DEBUG;
  const env = loadEnv(mode, process.cwd(), '');

  // PERFORMANCE: Define manual chunks for better code splitting
  const manualChunks = (id: string) => {
    if (
      id.includes('node_modules/react') ||
      id.includes('node_modules/use-sync-external-store')
    ) {
      return 'vendor-react';
    }
    if (
      id.includes('node_modules/@radix-ui') ||
      id.includes('node_modules/lucide-react')
    ) {
      return 'vendor-ui';
    }
    if (
      id.includes('node_modules/@xyflow') ||
      id.includes('node_modules/reactflow')
    ) {
      return 'vendor-flow';
    }
    if (id.includes('node_modules/@tanstack')) {
      return 'vendor-query';
    }
  };

  return {
    resolve: {
      alias: {
        '@': path.join(__dirname, 'src'),
      },
    },
    optimizeDeps: {
      exclude: ['@stackframe/react'],
      force: true,
    },
    build: {
      // PERFORMANCE: Target modern browsers for smaller bundles
      target: 'esnext',
      // PERFORMANCE: Minify with esbuild for speed
      minify: isBuild ? 'esbuild' : false,
      // PERFORMANCE: Generate sourcemap only in dev or if explicitly needed
      sourcemap: sourcemap,
      // PERFORMANCE: Budget limits to prevent bundle bloat (in kB)
      chunkSizeWarningLimit: 500,
      // PERFORMANCE: Enable rollup chunking for better caching
      rollupOptions: {
        output: {
          manualChunks,
          // Optimize chunk file names for caching
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash].[ext]',
          // PERFORMANCE: Use const functions for smaller output
          generatedCode: {
            constFunctions: true,
          },
        },
      },
    },
    plugins: [
      react(),
      electron({
        main: {
          // Shortcut of `build.lib.entry`
          entry: 'electron/main/index.ts',
          onstart(args) {
            if (process.env.VSCODE_DEBUG) {
              console.log(
                /* For `.vscode/.debug.script.mjs` */ '[startup] Electron App'
              );
              args.startup();
            } else {
              args.startup();
            }
          },
          vite: {
            build: {
              sourcemap,
              minify: isBuild,
              outDir: 'dist-electron/main',
              rollupOptions: {
                external: Object.keys(
                  'dependencies' in pkg ? pkg.dependencies : {}
                ),
              },
            },
          },
        },
        preload: {
          // Shortcut of `build.rollupOptions.input`.
          // Preload scripts may contain Web assets, so use the `build.rollupOptions.input` instead `build.lib.entry`.
          input: 'electron/preload/index.ts',
          vite: {
            build: {
              sourcemap: sourcemap ? 'inline' : undefined, // #332
              minify: isBuild,
              outDir: 'dist-electron/preload',
              rollupOptions: {
                external: Object.keys(
                  'dependencies' in pkg ? pkg.dependencies : {}
                ),
              },
            },
          },
        },
        // Ployfill the Electron and Node.js API for Renderer process.
        // If you want use Node.js in Renderer process, the `nodeIntegration` needs to be enabled in the Main process.
        // See 👉 https://github.com/electron-vite/vite-plugin-electron-renderer
        renderer: {},
      }),
    ],
    server: {
      open: false,
      ...(process.env.VSCODE_DEBUG &&
        (() => {
          const url = new URL(pkg.debug.env.VITE_DEV_SERVER_URL);
          return {
            host: url.hostname,
            port: +url.port,
            proxy: {
              '/api': {
                target: env.VITE_PROXY_URL,
                changeOrigin: true,
                // rewrite: path => path.replace(/^\/api/, ''),
              },
            },
          };
        })()),
      clearScreen: false,
    },
  };
});

process.on('SIGINT', () => {
  try {
    const backend = path.join(__dirname, 'backend');
    const pid = readFileSync(backend + '/runtime/run.pid', 'utf-8');
    process.kill(parseInt(pid), 'SIGINT');
  } catch (e) {
    console.log('no pid file');
    console.log(e);
  }
});
