import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  cacheDir: '../../.vite-cache/aiml02-viewer',
  server: { host: '0.0.0.0' },
})
