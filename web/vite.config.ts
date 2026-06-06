import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', 'VITE_')

  return {
    envDir: '..',
    plugins: [
      react(),
      tailwindcss(),

      VitePWA({
        registerType: 'autoUpdate',

        devOptions: {
          enabled: true,
        },

        workbox: {
          globPatterns: ['**/*.{js,css,html,png,svg,ico}'],
        },

        manifest: {
          name: 'logget',
          short_name: 'logget',
          description: 'AI-powered Micro-Journaling for Student Well-Being',

          theme_color: '#aa3bff',
          background_color: '#ffffff',

          display: 'standalone',

          scope: '/',
          start_url: '/',

          icons: [
            {
              src: '/pwa-192.png',
              sizes: '192x192',
              type: 'image/png',
            },
            {
              src: '/pwa-512.png',
              sizes: '512x512',
              type: 'image/png',
            },
          ],
        },
      }),
    ],
    server: {
      allowedHosts: [
        '*.ngrok-free.app',            // Ngrok Tunnel
        '*.trycloudflare.com',         // Cloudflare Tunnel
        '*.app.github.dev',            // GitHub Codespaces Tunnel
        '*.ngrok-free.dev',            // Ngrok Tunnel (duplicate for safety)
        'pointy-pointer-unlovable.ngrok-free.dev', // Specific Ngrok Tunnel
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