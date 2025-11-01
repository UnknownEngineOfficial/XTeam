import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  preview: {
    // Ensure preview uses the same port expected by tests/CI
    port: 3000,
  },
  build: {
    // Enable source maps for easier debugging of production bundles
    sourcemap: true,
  },
})