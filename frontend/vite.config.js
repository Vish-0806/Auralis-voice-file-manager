import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/command': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/voice': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/listener': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
