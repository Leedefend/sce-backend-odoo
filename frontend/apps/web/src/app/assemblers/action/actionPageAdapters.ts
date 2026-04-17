import type {
  ActionButtonVM,
  ActionGroupVM,
  ChipVM,
  ProjectionMetricVM,
} from './actionPageVm';

type Dict = Record<string, unknown>;

function asDict(value: unknown): Dict {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Dict;
}

export function toChipVM(value: unknown): ChipVM | null {
  const row = asDict(value);
  const key = String(row.key || '').trim();
  const label = String(row.label || row.key || '').trim();
  if (!key || !label) return null;
  return {
    key,
    label,
    field: String(row.field || '').trim() || undefined,
    context: asDict(row.context),
    contextRaw: String(row.contextRaw || row.context_raw || '').trim() || undefined,
    isDefault: row.isDefault === true || row.is_default === true,
  };
}

export function toActionButtonVM(value: unknown): ActionButtonVM | null {
  const row = asDict(value);
  const key = String(row.key || '').trim();
  const label = String(row.label || row.key || '').trim();
  if (!key || !label) return null;
  const enabledRaw = row.enabled;
  return {
    key,
    label,
    enabled: typeof enabledRaw === 'boolean' ? enabledRaw : true,
    hint: String(row.hint || '').trim() || undefined,
    kind: String(row.kind || '').trim() || undefined,
    actionId: Number.isFinite(Number(row.actionId ?? row.action_id)) ? Number(row.actionId ?? row.action_id) : null,
    methodName: String(row.methodName || row.method_name || '').trim() || undefined,
    model: String(row.model || '').trim() || undefined,
    target: String(row.target || '').trim() || undefined,
    url: String(row.url || '').trim() || undefined,
    selection: row.selection === 'single' || row.selection === 'multi' ? row.selection : 'none',
    context: asDict(row.context),
    domainRaw: String(row.domainRaw || row.domain_raw || '').trim() || undefined,
    mutation: asDict(row.mutation) as ActionButtonVM['mutation'],
    refreshPolicy: asDict(row.refreshPolicy || row.refresh_policy) as ActionButtonVM['refreshPolicy'],
  };
}

export function toActionGroupVM(value: unknown): ActionGroupVM | null {
  const row = asDict(value);
  const key = String(row.key || '').trim();
  const label = String(row.label || row.key || '').trim();
  const actionsRaw = Array.isArray(row.actions) ? row.actions : [];
  const actions = actionsRaw
    .map((item) => toActionButtonVM(item))
    .filter((item): item is ActionButtonVM => Boolean(item));
  if (!key || !label || !actions.length) return null;
  return { key, label, actions };
}

export function toProjectionMetricVM(value: unknown): ProjectionMetricVM | null {
  const row = asDict(value);
  const key = String(row.key || '').trim();
  const label = String(row.label || row.key || '').trim();
  if (!key || !label) return null;
  const valueText = String(row.value ?? '').trim();
  return {
    key,
    label,
    value: valueText,
    tone: String(row.tone || 'neutral').trim() || 'neutral',
  };
}

export function toAdvancedRowVM(value: unknown): { key: string; title: string; meta: string } | null {
  const row = asDict(value);
  const key = String(row.key || '').trim();
  const title = String(row.title || '').trim();
  const meta = String(row.meta || '').trim();
  if (!key || !title) return null;
  return {
    key,
    title,
    meta,
  };
}
