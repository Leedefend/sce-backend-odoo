import { computed, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type UseActionViewFilterComputedRuntimeOptions = {
  actionContract: Ref<{
    search?: {
      filters?: Array<Record<string, unknown>>;
      saved_filters?: Array<Record<string, unknown>>;
      group_by?: Array<Record<string, unknown>>;
    };
    surface_policies?: {
      filters_primary_max?: number;
    };
  } | null>;
  activeGroupByField: Ref<string>;
  parseContractContextRaw: (value: unknown) => Dict;
  isActionViewNumericToken: (value: unknown) => boolean;
  hasActionViewNoiseMarker: (key: unknown, label: unknown, domainRaw: unknown, contextRaw: unknown) => boolean;
};

function resolveGroupByFromContextRaw(value: unknown): string {
  const text = String(value || '').trim();
  if (!text) return '';
  const scalarMatch = text.match(/['"]group_by['"]\s*:\s*['"]([^'"]+)['"]/);
  if (scalarMatch?.[1]) return scalarMatch[1].trim();
  const listMatch = text.match(/['"]group_by['"]\s*:\s*\[\s*['"]([^'"]+)['"]/);
  return listMatch?.[1]?.trim() || '';
}

function resolveGroupByField(
  row: Record<string, unknown>,
  context: Dict,
  contextRaw: unknown,
  options?: { allowKeyFallback?: boolean },
): string {
  const direct = String(row.field || row.group_by || row.groupBy || row.group || '').trim();
  if (direct) return direct;
  const fromContext = context.group_by;
  if (typeof fromContext === 'string') return fromContext.trim();
  if (Array.isArray(fromContext)) return String(fromContext[0] || '').trim();
  const fromContextRaw = resolveGroupByFromContextRaw(contextRaw);
  if (fromContextRaw) return fromContextRaw;
  if (options?.allowKeyFallback) return String(row.key || row.name || '').trim();
  return '';
}

function isGroupByFilter(row: Record<string, unknown>, context: Dict): boolean {
  const hasGroupBy = Boolean(resolveGroupByField(row, context, row.context_raw));
  if (!hasGroupBy) return false;
  const domain = Array.isArray(row.domain) ? row.domain : [];
  const domainRaw = String(row.domain_raw || '').trim();
  return !domain.length && !domainRaw;
}

export function useActionViewFilterComputedRuntime(options: UseActionViewFilterComputedRuntimeOptions) {
  const contractFilterChips = computed(() => {
    const rows = options.actionContract.value?.search?.filters;
    if (!Array.isArray(rows)) return [];
    return rows
      .map((row) => {
        const key = String(row?.key || '').trim();
        const label = String(row?.label || row?.key || '').trim();
        if (!key || !label) return null;
        if (options.isActionViewNumericToken(key) || options.isActionViewNumericToken(label)) return null;
        if (options.hasActionViewNoiseMarker(key, label, row?.domain_raw, row?.context_raw)) return null;
        const domain = Array.isArray(row?.domain) ? row.domain : [];
        const domainRaw = String(row?.domain_raw || '').trim();
        const contextRaw = String(row?.context_raw || '').trim();
        const context = options.parseContractContextRaw(row?.context_raw);
        if (isGroupByFilter(row, context)) return null;
        return { key, label, domain, domainRaw, context, contextRaw };
      })
      .filter(Boolean)
      .slice(0, 8);
  });

  const filterPrimaryBudget = computed(() => {
    const raw = Number(options.actionContract.value?.surface_policies?.filters_primary_max ?? 5);
    if (!Number.isFinite(raw) || raw < 0) return 5;
    return Math.floor(raw);
  });

  const contractPrimaryFilterChips = computed(() =>
    contractFilterChips.value.slice(0, filterPrimaryBudget.value),
  );

  const contractOverflowFilterChips = computed(() =>
    contractFilterChips.value.slice(filterPrimaryBudget.value),
  );

  const contractSavedFilterChips = computed(() => {
    const rows = options.actionContract.value?.search?.saved_filters;
    if (!Array.isArray(rows)) return [];
    return rows
      .map((row, idx) => {
        const raw = row as Record<string, unknown>;
        const key = String(raw.key || raw.name || raw.xmlid || raw.xml_id || `saved_${idx + 1}`).trim();
        const label = String(raw.label || raw.name || key).trim();
        if (!key || !label) return null;
        if (options.isActionViewNumericToken(key) || options.isActionViewNumericToken(label)) return null;
        if (options.hasActionViewNoiseMarker(key, label, raw.domain_raw, raw.context_raw)) return null;
        const domain = Array.isArray(raw.domain) ? raw.domain : [];
        const domainRaw = String(raw.domain_raw || '').trim();
        const contextRaw = String(raw.context_raw || '').trim();
        const context = options.parseContractContextRaw(raw.context_raw);
        const isDefault = raw.default === true || raw.is_default === true;
        return { key, label, domain, domainRaw, context, contextRaw, isDefault };
      })
      .filter(Boolean)
      .slice(0, 12);
  });

  const savedFilterPrimaryChips = computed(() =>
    contractSavedFilterChips.value.slice(0, filterPrimaryBudget.value),
  );

  const savedFilterOverflowChips = computed(() =>
    contractSavedFilterChips.value.slice(filterPrimaryBudget.value),
  );

  const contractGroupByChips = computed(() => {
    const explicitRows = options.actionContract.value?.search?.group_by;
    const filterRows = options.actionContract.value?.search?.filters;
    const rows = [
      ...(Array.isArray(filterRows) ? filterRows.map((row) => ({ row, source: 'filter' as const })) : []),
      ...(Array.isArray(explicitRows) ? explicitRows.map((row) => ({ row, source: 'group' as const })) : []),
    ];
    const seen = new Set<string>();
    return rows
      .map((entry) => {
        const raw = entry.row as Record<string, unknown>;
        const contextRaw = String(raw.context_raw || '').trim();
        const context = options.parseContractContextRaw(contextRaw);
        const field = resolveGroupByField(raw, context, contextRaw, { allowKeyFallback: entry.source === 'group' });
        const label = String(raw.label || raw.string || raw.name || field).trim();
        if (!field || !label) return null;
        if (seen.has(field)) return null;
        seen.add(field);
        if (options.isActionViewNumericToken(field) || options.isActionViewNumericToken(label)) return null;
        const isDefault = raw.default === true || raw.is_default === true;
        return { key: field, field, label, context, contextRaw, isDefault };
      })
      .filter(Boolean)
      .slice(0, 12);
  });

  const groupByPrimaryChips = computed(() =>
    contractGroupByChips.value.slice(0, filterPrimaryBudget.value),
  );

  const groupByOverflowChips = computed(() =>
    contractGroupByChips.value.slice(filterPrimaryBudget.value),
  );

  const activeGroupByLabel = computed(() => {
    const field = options.activeGroupByField.value;
    if (!field) return '';
    const found = contractGroupByChips.value.find((chip) => String((chip as Dict).field || '') === field) as Dict | undefined;
    return String(found?.label || field);
  });

  return {
    contractFilterChips,
    filterPrimaryBudget,
    contractPrimaryFilterChips,
    contractOverflowFilterChips,
    contractSavedFilterChips,
    savedFilterPrimaryChips,
    savedFilterOverflowChips,
    contractGroupByChips,
    groupByPrimaryChips,
    groupByOverflowChips,
    activeGroupByLabel,
  };
}
