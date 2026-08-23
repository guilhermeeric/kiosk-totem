import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// Dev proxy: the frontend talks to the backend same-origin; the API paths are
// forwarded to the backend container/process. No CORS, no backend changes.
const API_PROXY_TARGET = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/items': API_PROXY_TARGET,
      '/carts': API_PROXY_TARGET,
      '/orders': API_PROXY_TARGET,
      '/health': API_PROXY_TARGET,
      '/openapi.json': API_PROXY_TARGET,
    },
  },
  test: {
    environment: 'happy-dom',
  },
})
