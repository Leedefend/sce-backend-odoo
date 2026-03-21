import { resolveActiveDb } from './services/dbContext';

const appEnv = String(import.meta.env.VITE_APP_ENV ?? 'dev').trim();
const envDb = String(import.meta.env.VITE_ODOO_DB ?? '').trim();
const isLocalHost = typeof window !== 'undefined'
  ? ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
  : false;
const runtimeDb = typeof window !== 'undefined'
  ? String(new URLSearchParams(window.location.search).get('db') || '').trim()
  : '';
// Do not auto-force a db by APP_ENV. Always prefer explicit VITE_ODOO_DB.
// Auto-forcing may cause token/db mismatch when frontend host is not localhost.
const enforcedDb = '';
const envDbNormalized = envDb.toLowerCase();
const localBlockedEnvDb = isLocalHost && envDbNormalized === 'sc_delivery_local' ? '' : envDb;
const allowLocalFallbackDb = appEnv === 'dev' || appEnv === 'test' || appEnv === 'local';
// For local dev/test only, fallback to sc_demo when db env is not explicitly set.
const localDefaultDb = allowLocalFallbackDb && !runtimeDb && !localBlockedEnvDb && isLocalHost ? 'sc_demo' : '';

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  appEnv,
  tenant: import.meta.env.VITE_TENANT ?? 'default',
  featureFlags: (import.meta.env.VITE_FEATURE_FLAGS ?? '')
    .split(',')
    .map((flag: string) => flag.trim())
    .filter(Boolean),
  odooDb: resolveActiveDb(runtimeDb || localBlockedEnvDb || enforcedDb || localDefaultDb),
};

// C1: 在开发模式下打印环境变量
if (import.meta.env.DEV) {
  console.group('[C1] 环境变量配置');
  console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
  console.log('VITE_ODOO_DB:', import.meta.env.VITE_ODOO_DB);
  console.log('URL db override:', runtimeDb);
  console.log('VITE_APP_ENV:', import.meta.env.VITE_APP_ENV);
  console.log('最终配置:', config);
  console.groupEnd();
}
