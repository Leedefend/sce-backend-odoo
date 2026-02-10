export interface TraceEvent {
  ts: number;
  trace_id: string;
  intent: string;
  status: 'ok' | 'error';
  event_type?: 'intent' | 'suggested_action';
  menu_id?: number;
  action_id?: number;
  model?: string;
  view_mode?: string;
  params_digest?: string;
  suggested_action_kind?: string;
  suggested_action_raw?: string;
  suggested_action_success?: boolean;
}

export interface SuggestedActionTraceFilter {
  kind?: string;
  success?: boolean;
  limit?: number;
  since_ts?: number;
}

export interface SuggestedActionTraceRow {
  ts: number;
  trace_id: string;
  kind: string;
  raw: string;
  success: boolean;
}

export interface SuggestedActionKindStat {
  kind: string;
  count: number;
}

const STORAGE_KEY = 'sc_frontend_traces_v0_3';
const MAX_ENTRIES = 200;
const TRACE_UPDATE_EVENT = 'sc:trace-updated';

export function recordTrace(event: TraceEvent) {
  const list = getTraceLog();
  list.unshift({ ...event, event_type: event.event_type || 'intent' });
  const sliced = list.slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sliced));
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(TRACE_UPDATE_EVENT));
  }
}

export function getTraceUpdateEventName() {
  return TRACE_UPDATE_EVENT;
}

export function recordSuggestedActionTrace(event: {
  trace_id?: string;
  kind: string;
  raw: string;
  success: boolean;
}) {
  recordTrace({
    ts: Date.now(),
    trace_id: event.trace_id || createTraceId(),
    intent: 'suggested_action.run',
    status: event.success ? 'ok' : 'error',
    event_type: 'suggested_action',
    suggested_action_kind: event.kind,
    suggested_action_raw: event.raw,
    suggested_action_success: event.success,
  });
}

export function getLatestSuggestedActionTrace(): TraceEvent | null {
  const list = getTraceLog();
  for (const item of list) {
    if (item.event_type === 'suggested_action') {
      return item;
    }
  }
  return null;
}

function normalizeSuggestedActionTrace(event: TraceEvent): SuggestedActionTraceRow | null {
  if (event.event_type !== 'suggested_action') return null;
  const kind = String(event.suggested_action_kind || '').trim();
  const raw = String(event.suggested_action_raw || '').trim();
  const success = event.suggested_action_success === true;
  if (!kind) return null;
  return {
    ts: Number(event.ts || 0),
    trace_id: String(event.trace_id || '').trim(),
    kind,
    raw,
    success,
  };
}

export function listSuggestedActionTraces(filter: SuggestedActionTraceFilter = {}): SuggestedActionTraceRow[] {
  const limit = Math.max(1, Number(filter.limit || 50));
  const targetKind = String(filter.kind || '').trim().toLowerCase();
  const expectedSuccess = typeof filter.success === 'boolean' ? filter.success : null;
  const sinceTs = Number(filter.since_ts || 0);
  const rows: SuggestedActionTraceRow[] = [];

  for (const event of getTraceLog()) {
    const row = normalizeSuggestedActionTrace(event);
    if (!row) continue;
    if (sinceTs > 0 && row.ts < sinceTs) continue;
    if (targetKind && row.kind.toLowerCase() !== targetKind) continue;
    if (expectedSuccess !== null && row.success !== expectedSuccess) continue;
    rows.push(row);
    if (rows.length >= limit) break;
  }

  return rows;
}

export function exportSuggestedActionTraces(filter: SuggestedActionTraceFilter = {}): string {
  const items = listSuggestedActionTraces(filter);
  const successCount = items.filter((item) => item.success).length;
  const failureCount = items.length - successCount;
  const payload = {
    filter: {
      kind: String(filter.kind || '').trim() || undefined,
      success: typeof filter.success === 'boolean' ? filter.success : undefined,
      limit: Math.max(1, Number(filter.limit || 50)),
      since_ts: Number(filter.since_ts || 0) > 0 ? Number(filter.since_ts) : undefined,
    },
    summary: {
      total: items.length,
      success_count: successCount,
      failure_count: failureCount,
      top_k: rankSuggestedActionKinds(5),
    },
    items,
  };
  return JSON.stringify(payload, null, 2);
}

export function summarizeSuggestedActionTraceFilter(filter: SuggestedActionTraceFilter = {}): string {
  const parts: string[] = [];
  const kind = String(filter.kind || '').trim();
  if (kind) parts.push(`kind=${kind}`);
  if (typeof filter.success === 'boolean') parts.push(`success=${filter.success ? 'true' : 'false'}`);
  if (Number(filter.since_ts || 0) > 0) parts.push(`since_ts=${Math.floor(Number(filter.since_ts))}`);
  return parts.join(', ');
}

export function rankSuggestedActionKinds(limit = 5): SuggestedActionKindStat[] {
  const stats = new Map<string, number>();
  for (const row of listSuggestedActionTraces({ limit: MAX_ENTRIES })) {
    const key = row.kind;
    stats.set(key, (stats.get(key) || 0) + 1);
  }
  return [...stats.entries()]
    .map(([kind, count]) => ({ kind, count }))
    .sort((a, b) => b.count - a.count || a.kind.localeCompare(b.kind))
    .slice(0, Math.max(1, Number(limit || 5)));
}

export function createTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export function getTraceLog(): TraceEvent[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function digestParams(params: Record<string, unknown>) {
  try {
    return JSON.stringify(params);
  } catch {
    return '';
  }
}
