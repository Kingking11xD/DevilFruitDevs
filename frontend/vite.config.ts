import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxies requests from the React frontend to the FastAPI backend[cite: 1]
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/customers': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})