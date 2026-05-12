import { resolveActiveDb } from './services/dbContext';

const appEnv = String(import.meta.env.VITE_APP_ENV ?? 'dev').trim();
const envDb = String(import.meta.env.VITE_ODOO_DB ?? '').trim();
const isLocalHost = typeof window !== 'undefined'
  ? ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
  : false;
const isLocalDevPort = typeof window !== 'undefined'
  ? ['18081', '5174', '8070'].includes(window.location.port)
  : false;
const isLocalDevRuntime = isLocalHost && isLocalDevPort;
const runtimeDbRaw = typeof window !== 'undefined'
  ? String(new URLSearchParams(window.location.search).get('db') || '').trim()
  : '';
const runtimeDb = isLocalHost && isLocalDevPort && ['sc_delivery_local', 'sc_prod_sim'].includes(runtimeDbRaw.toLowerCase())
  ? ''
  : runtimeDbRaw;
// Do not auto-force a db by APP_ENV. Always prefer explicit VITE_ODOO_DB.
// Auto-forcing may cause token/db mismatch when frontend host is not localhost.
const enforcedDb = '';
const envDbNormalized = envDb.toLowerCase();
const localBlockedProductionDb = isLocalHost && ['sc_delivery_local', 'sc_prod_sim'].includes(envDbNormalized);
const localBlockedEnvDb = localBlockedProductionDb ? '' : envDb;
const allowLocalFallbackDb = isLocalHost || appEnv === 'dev' || appEnv === 'test' || appEnv === 'local';
// For local dev/test only, fallback to sc_demo when db env is not explicitly set.
const localDefaultDb = allowLocalFallbackDb && !runtimeDb && !localBlockedEnvDb && isLocalHost ? 'sc_demo' : '';
const localDevPinnedDb = isLocalDevRuntime ? 'sc_demo' : '';
const pinnedDb = localDevPinnedDb || localBlockedEnvDb || enforcedDb || runtimeDb;

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  appEnv,
  tenant: import.meta.env.VITE_TENANT ?? 'default',
  featureFlags: (import.meta.env.VITE_FEATURE_FLAGS ?? '')
    .split(',')
    .map((flag: string) => flag.trim())
    .filter(Boolean),
  odooDb: pinnedDb || (localBlockedProductionDb ? localDefaultDb : resolveActiveDb(localDefaultDb)),
  odooDbPinned: Boolean(pinnedDb),
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
