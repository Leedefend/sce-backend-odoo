import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

const port = Number(process.env.VITE_DEV_PORT ?? 5174);
const host = process.env.VITE_DEV_HOST ?? '0.0.0.0';
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8069';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@sc/schema': path.resolve(__dirname, '../../packages/schema/src/index.ts'),
    },
  },
  server: {
    host,
    port,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
