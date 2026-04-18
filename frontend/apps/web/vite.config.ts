import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

const port = Number(process.env.VITE_DEV_PORT ?? 5174);
const host = process.env.VITE_DEV_HOST ?? '0.0.0.0';
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8069';
const hmrHost = process.env.VITE_HMR_HOST ?? (host === '0.0.0.0' ? '127.0.0.1' : host);
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT ?? port);
const hmrProtocol = process.env.VITE_HMR_PROTOCOL || undefined;
const watchUsePolling = /^(1|true|yes)$/i.test(String(process.env.VITE_WATCH_USE_POLLING ?? ''));
const watchInterval = Number(process.env.VITE_WATCH_INTERVAL ?? 200);
const watchAwaitWriteMs = Number(process.env.VITE_WATCH_AWAIT_WRITE_MS ?? 150);

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
    hmr: {
      host: hmrHost,
      clientPort: hmrClientPort,
      protocol: hmrProtocol,
    },
    watch: watchUsePolling
      ? {
          usePolling: true,
          interval: watchInterval,
          awaitWriteFinish: {
            stabilityThreshold: watchAwaitWriteMs,
            pollInterval: Math.max(50, Math.floor(watchInterval / 2)),
          },
        }
      : undefined,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
