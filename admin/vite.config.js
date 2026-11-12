import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['wallets.edulibris.com'],
    hmr: {
      host: 'wallets.edulibris.com',
      protocol: 'wss',
      clientPort: 443,
    },
  },
})
