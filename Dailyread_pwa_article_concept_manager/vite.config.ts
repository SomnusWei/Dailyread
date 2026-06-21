import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { resolve } from 'path'

export default defineConfig({
  define: {
    __API_BASE_URL__: JSON.stringify('/api')
  },
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: '每日阅读管理器',
        short_name: '每日阅读',
        description: '文章与概念管理工具',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#4f46e5',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{html,js,css,svg,png}']
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      // WebDAV 代理
      '/webdav': {
        target: 'https://dav.jianguoyun.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/webdav/, '')
      },
      // 后端 API 代理
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true
      }
    }
  }
})
