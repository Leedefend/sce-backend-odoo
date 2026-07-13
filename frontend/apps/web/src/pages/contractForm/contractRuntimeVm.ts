import type { ContractAction } from './types';

function recordOrEmpty(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

export function collectRuntimeCapabilities(session: {
  capabilities?: unknown[];
  capabilityCatalog?: Record<string, { key?: unknown; state?: unknown; capability_state?: unknown }>;
}) {
  const out = new Set<string>();
  (session.capabilities || []).forEach((key) => {
    const normalized = String(key || '').trim();
    if (normalized) out.add(normalized);
  });
  Object.values(session.capabilityCatalog || {}).forEach((meta) => {
    const key = String(meta?.key || '').trim();
    if (!key) return;
    const state = String(meta?.state || '').trim().toUpperCase();
    const capState = String(meta?.capability_state || '').trim().toLowerCase();
    if (state === 'LOCKED' || capState === 'deny') return;
    out.add(key);
  });
  return out;
}

export function collectRuntimeUserGroups(user: { groups_xmlids?: unknown } | null | undefined) {
  return Array.isArray(user?.groups_xmlids)
    ? user.groups_xmlids.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
}

export function normalizeContractWarnings(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      if (typeof row === 'string') return row;
      if (row && typeof row === 'object') {
        return String((row as Record<string, unknown>).message || (row as Record<string, unknown>).code || '');
      }
      return '';
    })
    .map((item) => item.trim())
    .filter((item) => Boolean(item) && !item.startsWith('access_policy:'));
}

export function normalizeSearchFilters(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const item = row && typeof row === 'object' && !Array.isArray(row)
        ? row as Record<string, unknown>
        : {};
      return {
        key: String(item.key || '').trim(),
        label: String(item.label || item.key || '').trim(),
        domainRaw: String(item.domain_raw || '').trim(),
        contextRaw: String(item.context_raw || '').trim(),
      };
    })
    .filter((row) => row.key && row.label);
}

export function resolveBusinessCategoryContext(params: {
  contractRecord: unknown;
  routeQuery: Record<string, unknown>;
  relationBusinessCategoryLabel: string;
}) {
  const contractRecord = recordOrEmpty(params.contractRecord);
  const head = recordOrEmpty(contractRecord.head);
  const headContext = recordOrEmpty(head.context);
  const contractContext = recordOrEmpty(contractRecord.context);
  const query = params.routeQuery;
  return {
    label: String(
      query.current_business_category_label
      || query.default_business_category_label
      || headContext.current_business_category_label
      || headContext.default_business_category_label
      || contractContext.current_business_category_label
      || contractContext.default_business_category_label
      || params.relationBusinessCategoryLabel
      || '',
    ).trim(),
    code: String(
      query.current_business_category_code
      || query.default_business_category_code
      || headContext.current_business_category_code
      || headContext.default_business_category_code
      || contractContext.current_business_category_code
      || contractContext.default_business_category_code
      || '',
    ).trim(),
  };
}

export function buildWorkflowTransitions(params: {
  rows: unknown;
  actions: ContractAction[];
  profile: 'create' | 'edit' | 'readonly';
  showHud: boolean;
}) {
  if (!Array.isArray(params.rows)) return [];
  if (params.profile === 'create') return [];
  const headerActionKeys = new Set(
    params.actions
      .filter((item) => item.level === 'header' || item.level === 'toolbar')
      .map((item) => item.key),
  );
  const transitions = params.rows.map((raw, idx) => {
    const row = raw && typeof raw === 'object' && !Array.isArray(raw)
      ? raw as Record<string, { label?: unknown; name?: unknown; kind?: unknown } | unknown>
      : {};
    const trigger = row.trigger && typeof row.trigger === 'object' && !Array.isArray(row.trigger)
      ? row.trigger as Record<string, unknown>
      : {};
    const triggerLabel = String(trigger.label || '').trim();
    const triggerName = String(trigger.name || '').trim();
    const triggerKind = String(trigger.kind || '').trim().toLowerCase();
    const action = params.actions.find((item) => {
      if (triggerKind && item.kind && item.kind !== triggerKind) return false;
      if (triggerName && (item.methodName === triggerName || item.key.includes(triggerName))) return true;
      if (triggerLabel && item.label === triggerLabel) return true;
      return false;
    }) || null;
    return {
      key: `wf_${idx}`,
      label: triggerLabel || triggerName || `transition_${idx + 1}`,
      notes: String(row.notes || ''),
      action,
    };
  });
  if (params.showHud) return transitions;
  return transitions.filter((item) => {
    const label = String(item.label || '').trim();
    if (!item.action) return false;
    if (item.action?.key && headerActionKeys.has(item.action.key)) return false;
    if (/^\d+$/.test(label)) return false;
    return true;
  });
}
