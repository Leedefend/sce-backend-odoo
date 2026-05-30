const DB_SCOPE = String(import.meta.env.VITE_APP_ENV || 'default').trim() || 'default';
const ACTIVE_DB_STORAGE_KEY = `sc_active_db:${DB_SCOPE}`;
const LOCAL_DEV_PORTS = new Set(['18081', '5174', '8070', '8073']);
const LOCAL_DEV_BLOCKED_DBS = new Set(['sc_prod_sim', 'sc_delivery_local']);
const ENV_DB = String(import.meta.env.VITE_ODOO_DB ?? '').trim();
const PLATFORM_ADMIN_DB = String(import.meta.env.VITE_PLATFORM_ADMIN_DB ?? '').trim();
const ENV_DB_LOCKED = Boolean(ENV_DB) && String(import.meta.env.VITE_ODOO_DB_LOCKED ?? '1').trim() !== '0';

function normalizeDb(value: unknown): string {
  const db = String(value || '').trim();
  return db;
}

function isLocalDevRuntime(): boolean {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname;
  return (
    (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0')
    && LOCAL_DEV_PORTS.has(window.location.port)
  );
}

export function isPlatformAdminEntryRuntime(): boolean {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return window.location.pathname.startsWith('/platform-admin') || params.get('platform_admin') === '1';
}

function isBlockedLocalDevDb(db: string): boolean {
  return isLocalDevRuntime() && LOCAL_DEV_BLOCKED_DBS.has(db.toLowerCase());
}

function sanitizeDb(db: string): string {
  if (!db) return '';
  return isBlockedLocalDevDb(db) ? '' : db;
}

function clearStoredDb(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(ACTIVE_DB_STORAGE_KEY);
  localStorage.removeItem(ACTIVE_DB_STORAGE_KEY);
}

function readDbFromQuery(): string {
  if (typeof window === 'undefined') return '';
  const db = normalizeDb(new URLSearchParams(window.location.search).get('db'));
  return sanitizeDb(db);
}

function readDbFromStorage(): string {
  if (typeof window === 'undefined') return '';
  const sessionDb = normalizeDb(sessionStorage.getItem(ACTIVE_DB_STORAGE_KEY));
  if (sessionDb) {
    if (isBlockedLocalDevDb(sessionDb)) {
      clearStoredDb();
      return '';
    }
    return sessionDb;
  }
  const localDb = normalizeDb(localStorage.getItem(ACTIVE_DB_STORAGE_KEY));
  if (isBlockedLocalDevDb(localDb)) {
    clearStoredDb();
    return '';
  }
  return localDb;
}

export function resolveActiveDb(fallbackDb = ''): string {
  return readDbFromQuery() || readDbFromStorage() || normalizeDb(fallbackDb);
}

export function resolveConfiguredDb(fallbackDb = ''): string {
  const envDb = sanitizeDb(ENV_DB);
  if (isPlatformAdminEntryRuntime() && PLATFORM_ADMIN_DB) {
    return sanitizeDb(PLATFORM_ADMIN_DB);
  }
  if (ENV_DB_LOCKED) {
    return envDb;
  }
  return resolveActiveDb(envDb || fallbackDb);
}

export function resolveLoginRoutingDb(): string {
  return isPlatformAdminEntryRuntime() ? sanitizeDb(PLATFORM_ADMIN_DB) : '';
}

export function isConfiguredDbPinned(): boolean {
  return Boolean((isPlatformAdminEntryRuntime() && PLATFORM_ADMIN_DB) || ENV_DB_LOCKED);
}

export function setActiveDb(db: string, syncUrl = false): void {
  const normalized = normalizeDb(db);
  if (!normalized || typeof window === 'undefined') return;
  if (isBlockedLocalDevDb(normalized)) {
    clearStoredDb();
    return;
  }
  sessionStorage.setItem(ACTIVE_DB_STORAGE_KEY, normalized);
  localStorage.setItem(ACTIVE_DB_STORAGE_KEY, normalized);
  if (!syncUrl) return;
  const url = new URL(window.location.href);
  if (url.searchParams.get('db') === normalized) return;
  url.searchParams.set('db', normalized);
  window.history.replaceState(null, '', url.toString());
}
