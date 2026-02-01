import { config } from '../config';
import { useSessionStore } from '../stores/session';

export class ApiError extends Error {
  status: number;
  traceId?: string;

  constructor(message: string, status: number, traceId?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.traceId = traceId;
  }
}

function generateTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}) {
  const session = useSessionStore();
  const headers = new Headers(options.headers ?? {});
  const existingTrace = headers.get('x-trace-id');
  const traceId = existingTrace || generateTraceId();

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
    credentials: 'include',
  });

  if (response.status === 401) {
    session.clearSession();
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = `/login?redirect=${redirect}`;
    }
    throw new ApiError('unauthorized', 401);
  }

  if (!response.ok) {
    let message = `request failed: ${response.status}`;
    let traceId: string | undefined;
    try {
      const body = await response.json();
      message = body?.error?.message || body?.message || message;
      traceId = body?.meta?.trace_id || body?.meta?.traceId || body?.trace_id;
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new ApiError(message, response.status, traceId);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
