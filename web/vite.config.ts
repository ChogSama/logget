import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', 'VITE_')

  return {
    envDir: '..',
    plugins: [react(), tailwindcss()],
    server: {
      allowedHosts: [
        '*.ngrok-free.app',            // Ngrok Tunnel
        '*.trycloudflare.com',         // Cloudflare Tunnel
        '*.app.github.dev'             // GitHub Codespaces Tunnel
      ],
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})