import { config } from '../config';
import { useSessionStore } from '../stores/session';

function generateTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}) {
  const session = useSessionStore();
  const traceId = generateTraceId();
  const headers = new Headers(options.headers ?? {});

  headers.set('Content-Type', 'application/json');
  headers.set('x-trace-id', traceId);
  headers.set('x-tenant', config.tenant);

  if (config.odooDb) {
    headers.set('X-Odoo-DB', config.odooDb);
  }

  if (session.token) {
    headers.set('Authorization', `Bearer ${session.token}`);
  }

  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    session.clearSession();
    throw new Error('unauthorized');
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
