import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const cloudProxyTarget =
    env.VITE_API_PROXY_TARGET ||
    'https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io'
  const localProxyTarget =
    env.VITE_API_PROXY_TARGET_LOCAL ||
    'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
      globals: true,
      clearMocks: true,
    },
    server: {
      proxy: {
        '/api-local': {
          target: localProxyTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api-local/, ''),
        },
        '/api-cloud': {
          target: cloudProxyTarget,
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path.replace(/^\/api-cloud/, ''),
        },
        '/api': {
          target: cloudProxyTarget,
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
