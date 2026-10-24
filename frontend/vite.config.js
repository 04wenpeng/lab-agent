import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    // 允许局域网/虚拟局域网内的其他人访问（0.0.0.0:5173）
    host: true,
    port: 5173,
    // 允许用主机名访问（Vite 7+ 默认拦截未知 Host，这里放行本机名和 .local）
    allowedHosts: ['desktop-m0b255v', 'desktop-m0b255v.local', '.local'],
    // 忽略编辑器/工具写入时产生的临时目录，避免 watcher 命中 EBUSY 直接崩掉
    watch: {
      ignored: ['**/*.tmpdir/**', '**/.*.tmp', '**/.git/**']
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001', //  /api -> http://127.0.0.1:8001/api
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://127.0.0.1:8001', //  /uploads -> http://127.0.0.1:8001/uploads
        changeOrigin: true
      }
    }
  }
})
