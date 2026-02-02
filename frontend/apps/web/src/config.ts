export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8070',
  appEnv: import.meta.env.VITE_APP_ENV ?? 'dev',
  tenant: import.meta.env.VITE_TENANT ?? 'default',
  featureFlags: (import.meta.env.VITE_FEATURE_FLAGS ?? '')
    .split(',')
    .map((flag: string) => flag.trim())
    .filter(Boolean),
  // 临时硬编码数据库名，用于测试
  odooDb: import.meta.env.VITE_ODOO_DB ?? 'sc_demo',
};
