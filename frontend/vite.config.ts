import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor: React core
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Vendor: charting (largest dependency)
          'vendor-charts': ['recharts'],
          // Vendor: utilities
          'vendor-utils': ['axios', 'date-fns', 'lucide-react', 'clsx'],
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
})
