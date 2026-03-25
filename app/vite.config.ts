import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],

  // Prevent vite from obscuring Rust errors
  clearScreen: false,

  server: {
    port: 5173,
    // Tauri expects a fixed port
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
    watch: {
      ignored: ['**/.venv/**', '**/server/**', '**/src-tauri/**'],
    },
  },

  // Env variables starting with TAURI_ are exposed to the app
  envPrefix: ['VITE_', 'TAURI_'],

  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Tauri uses Chromium on Windows/Linux and WebKit on macOS
    // Produce separate sourcemaps for better debugging
    sourcemap: !!process.env.TAURI_DEBUG,
    // Don't minify for debug builds
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    target: process.env.TAURI_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
  },
});
