import { isConfiguredDbPinned, isPlatformAdminEntryRuntime, resolveConfiguredDb } from './services/dbContext';

const appEnv = String(import.meta.env.VITE_APP_ENV ?? 'dev').trim();
const envDb = String(import.meta.env.VITE_ODOO_DB ?? '').trim();
const platformAdminDb = String(import.meta.env.VITE_PLATFORM_ADMIN_DB ?? '').trim();
const envDbLocked = envDb && String(import.meta.env.VITE_ODOO_DB_LOCKED ?? '1').trim() !== '0';
const startupRootXmlid = String(import.meta.env.VITE_STARTUP_ROOT_XMLID ?? 'smart_construction_core.menu_sc_root').trim();
const appTitle = String(import.meta.env.VITE_APP_TITLE ?? '智能施工企业管理平台').trim();
const appBrand = {
  name: String(import.meta.env.VITE_BRAND_NAME ?? appTitle).trim(),
  subtitle: String(import.meta.env.VITE_BRAND_SUBTITLE ?? '工程项目全生命周期管理系统').trim(),
  slogan: String(import.meta.env.VITE_BRAND_SLOGAN ?? '让项目透明 · 让合同可控 · 让资金协同 · 让风险可预警').trim(),
  productBadge: String(import.meta.env.VITE_PRODUCT_BADGE ?? 'SCEMS · v1.0').trim(),
  kicker: String(import.meta.env.VITE_BRAND_KICKER ?? '智能建造 · 企业级管理').trim(),
  footerPrimary: String(import.meta.env.VITE_FOOTER_PRIMARY ?? '© 2025 SCEMS Platform').trim(),
  footerSecondary: String(import.meta.env.VITE_FOOTER_SECONDARY ?? 'Smart Construction Enterprise Management System').trim(),
  shellLogoText: String(import.meta.env.VITE_SHELL_LOGO_TEXT ?? 'SC').trim(),
  capabilities: {
    project: String(import.meta.env.VITE_CAPABILITY_PROJECT ?? '项目全过程管理').trim(),
    contractCost: String(import.meta.env.VITE_CAPABILITY_CONTRACT_COST ?? '合同成本联动').trim(),
    fund: String(import.meta.env.VITE_CAPABILITY_FUND ?? '资金支付协同').trim(),
    risk: String(import.meta.env.VITE_CAPABILITY_RISK ?? '风险预警驾驶舱').trim(),
  },
  valueLines: [
    String(import.meta.env.VITE_VALUE_LINE_1 ?? '让项目透明').trim(),
    String(import.meta.env.VITE_VALUE_LINE_2 ?? '让合同可控').trim(),
    String(import.meta.env.VITE_VALUE_LINE_3 ?? '让资金协同').trim(),
    String(import.meta.env.VITE_VALUE_LINE_4 ?? '让风险可预警').trim(),
  ].filter(Boolean),
};
const isLocalHost = typeof window !== 'undefined'
  ? ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
  : false;
const isLocalDevPort = typeof window !== 'undefined'
  ? ['18081', '5174', '8070', '8073'].includes(window.location.port)
  : false;
const isLocalDevRuntime = isLocalHost && isLocalDevPort;
const runtimeDbRaw = typeof window !== 'undefined'
  ? String(new URLSearchParams(window.location.search).get('db') || '').trim()
  : '';
const isPlatformAdminEntry = isPlatformAdminEntryRuntime();
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
// For local dev/test only, fallback to the restored daily development DB.
const localDefaultDb = allowLocalFallbackDb && !runtimeDb && !localBlockedEnvDb && isLocalHost ? 'sc_demo' : '';
const localDevPinnedDb = isLocalDevRuntime && !runtimeDb && !localBlockedEnvDb ? 'sc_demo' : '';
const pinnedDb = isPlatformAdminEntry && platformAdminDb
  ? platformAdminDb
  : envDbLocked ? localBlockedEnvDb : runtimeDb || localBlockedEnvDb || enforcedDb || localDevPinnedDb;

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  appEnv,
  tenant: import.meta.env.VITE_TENANT ?? 'default',
  featureFlags: (import.meta.env.VITE_FEATURE_FLAGS ?? '')
    .split(',')
    .map((flag: string) => flag.trim())
    .filter(Boolean),
  odooDb: pinnedDb || (localBlockedProductionDb ? localDefaultDb : resolveConfiguredDb(localDefaultDb)),
  odooDbPinned: Boolean(pinnedDb) || isConfiguredDbPinned(),
  platformAdminDb,
  isPlatformAdminEntry,
  startupRootXmlid,
  appTitle,
  appBrand,
};

// C1: 在开发模式下打印环境变量
if (import.meta.env.DEV) {
  console.group('[C1] 环境变量配置');
  console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
  console.log('VITE_ODOO_DB:', import.meta.env.VITE_ODOO_DB);
  console.log('VITE_ODOO_DB_LOCKED:', import.meta.env.VITE_ODOO_DB_LOCKED);
  console.log('VITE_PLATFORM_ADMIN_DB:', import.meta.env.VITE_PLATFORM_ADMIN_DB);
  console.log('VITE_STARTUP_ROOT_XMLID:', import.meta.env.VITE_STARTUP_ROOT_XMLID);
  console.log('VITE_APP_TITLE:', import.meta.env.VITE_APP_TITLE);
  console.log('Platform admin entry:', isPlatformAdminEntry);
  console.log('URL db override:', runtimeDb);
  console.log('VITE_APP_ENV:', import.meta.env.VITE_APP_ENV);
  console.log('最终配置:', config);
  console.groupEnd();
}
