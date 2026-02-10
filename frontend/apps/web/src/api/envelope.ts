import type { IntentEnvelope } from '@sc/schema';

export type IntentEnvelopeError = {
  code?: string;
  reason_code?: string;
  message?: string;
  hint?: string;
  kind?: string;
  error_category?: string;
  suggested_action?: string;
  retryable?: boolean;
  trace_id?: string;
  details?: Record<string, unknown>;
};

export type ParsedIntentEnvelope<T> = {
  data: T;
  meta: Record<string, unknown>;
  ok: boolean;
  error?: IntentEnvelopeError;
  hasEnvelope: boolean;
};

function isObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object';
}

function parseMeta(raw: unknown): Record<string, unknown> {
  return isObject(raw) ? raw : {};
}

function parseError(raw: unknown): IntentEnvelopeError | undefined {
  if (!isObject(raw)) return undefined;
  return {
    code: typeof raw.code === 'string' ? raw.code : undefined,
    reason_code: typeof raw.reason_code === 'string' ? raw.reason_code : undefined,
    message: typeof raw.message === 'string' ? raw.message : undefined,
    hint: typeof raw.hint === 'string' ? raw.hint : undefined,
    kind: typeof raw.kind === 'string' ? raw.kind : undefined,
    error_category: typeof raw.error_category === 'string' ? raw.error_category : undefined,
    suggested_action: typeof raw.suggested_action === 'string' ? raw.suggested_action : undefined,
    retryable: typeof raw.retryable === 'boolean' ? raw.retryable : undefined,
    trace_id: typeof raw.trace_id === 'string' ? raw.trace_id : undefined,
    details: isObject(raw.details) ? raw.details : undefined,
  };
}

export function parseIntentEnvelope<T>(body: IntentEnvelope<T> | T): ParsedIntentEnvelope<T> {
  if (!isObject(body)) {
    return { data: body as T, meta: {}, ok: true, hasEnvelope: false };
  }

  const hasEnvelope = ['ok', 'data', 'meta', 'error', 'status', 'code'].some((key) => key in body);
  const hasData = 'data' in body;
  const payload = body as IntentEnvelope<T> & { error?: unknown; meta?: unknown; ok?: boolean };
  const parsedError = parseError(payload.error);
  const fallbackError = payload.ok === false && !parsedError ? parseError(body) : undefined;
  return {
    data: hasData ? (payload.data as T) : (body as T),
    meta: parseMeta(payload.meta),
    ok: payload.ok !== false,
    error: parsedError || fallbackError,
    hasEnvelope,
  };
}
