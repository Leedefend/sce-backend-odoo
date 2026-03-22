const DB_SCOPE = String(import.meta.env.VITE_APP_ENV || 'default').trim() || 'default';
const ACTIVE_DB_STORAGE_KEY = `sc_active_db:${DB_SCOPE}`;

function normalizeDb(value: unknown): string {
  const db = String(value || '').trim();
  return db;
}

function readDbFromQuery(): string {
  if (typeof window === 'undefined') return '';
  return normalizeDb(new URLSearchParams(window.location.search).get('db'));
}

function readDbFromStorage(): string {
  if (typeof window === 'undefined') return '';
  const sessionDb = normalizeDb(sessionStorage.getItem(ACTIVE_DB_STORAGE_KEY));
  if (sessionDb) return sessionDb;
  return normalizeDb(localStorage.getItem(ACTIVE_DB_STORAGE_KEY));
}

export function resolveActiveDb(fallbackDb = ''): string {
  return readDbFromQuery() || readDbFromStorage() || normalizeDb(fallbackDb);
}

export function setActiveDb(db: string, syncUrl = false): void {
  const normalized = normalizeDb(db);
  if (!normalized || typeof window === 'undefined') return;
  sessionStorage.setItem(ACTIVE_DB_STORAGE_KEY, normalized);
  localStorage.setItem(ACTIVE_DB_STORAGE_KEY, normalized);
  if (!syncUrl) return;
  const url = new URL(window.location.href);
  if (url.searchParams.get('db') === normalized) return;
  url.searchParams.set('db', normalized);
  window.history.replaceState(null, '', url.toString());
}
