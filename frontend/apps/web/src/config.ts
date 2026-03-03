const appEnv = String(import.meta.env.VITE_APP_ENV ?? 'dev').trim();
const envDb = String(import.meta.env.VITE_ODOO_DB ?? '').trim();
const isLocalHost = typeof window !== 'undefined'
  ? ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
  : false;
// Delivery defaults to sc_delivery_local only on non-local hosts.
// Local dev may run against sc_demo/sc_* databases and must not be hard-bound.
const enforcedDb = appEnv === 'delivery' && !isLocalHost ? 'sc_delivery_local' : '';

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8070',
  appEnv,
  tenant: import.meta.env.VITE_TENANT ?? 'default',
  featureFlags: (import.meta.env.VITE_FEATURE_FLAGS ?? '')
    .split(',')
    .map((flag: string) => flag.trim())
    .filter(Boolean),
  odooDb: envDb || enforcedDb,
};

// C1: 在开发模式下打印环境变量
if (import.meta.env.DEV) {
  console.group('[C1] 环境变量配置');
  console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
  console.log('VITE_ODOO_DB:', import.meta.env.VITE_ODOO_DB);
  console.log('VITE_APP_ENV:', import.meta.env.VITE_APP_ENV);
  console.log('最终配置:', config);
  console.groupEnd();
}
