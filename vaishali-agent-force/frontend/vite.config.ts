import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Forward /api/* to the FastAPI backend (port 8077)
      // No rewrite — backend router is mounted at /api prefix
      '/api': {
        target: 'http://localhost:8077',
        changeOrigin: true,
      },
    },
  },
})
