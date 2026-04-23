type Dict = Record<string, unknown>;

type FilterChip = {
  key: string;
  domain: unknown[];
  domainRaw: string;
  context: Dict;
  contextRaw: string;
};

type GroupByChip = {
  field: string;
  context: Dict;
  contextRaw: string;
};

function findChipByKey<T extends { key: string }>(chips: T[], key: string): T | null {
  if (!key) return null;
  return chips.find((chip) => chip.key === key) || null;
}

function findGroupByChip(chips: GroupByChip[], field: string): GroupByChip | null {
  if (!field) return null;
  return chips.find((chip) => chip.field === field) || null;
}

export function resolveDefaultSortFromContract(contractFields: Dict): string {
  const fieldNames = new Set(Object.keys(contractFields || {}));
  const segments: string[] = [];
  if (fieldNames.has('write_date')) segments.push('write_date desc');
  segments.push('id desc');
  return segments.join(',');
}

export type ActionViewListProfileShape = {
  columns?: string[];
  row_secondary?: string;
};

export function uniqueFields(fields: string[]): string[] {
  const seen = new Set<string>();
  return fields.filter((field) => {
    if (!field) return false;
    if (seen.has(field)) return false;
    seen.add(field);
    return true;
  });
}

export function resolveRequestedFields(
  contractFields: string[],
  profile: ActionViewListProfileShape | null,
): string[] {
  const profileColumns = profile?.columns ?? [];
  const secondary = profile?.row_secondary ? [profile.row_secondary] : [];
  return uniqueFields([...profileColumns, ...secondary, ...contractFields]);
}

export function resolveFilterDomain(chips: FilterChip[], key: string): unknown[] {
  return findChipByKey(chips, key)?.domain || [];
}

export function resolveFilterDomainRaw(chips: FilterChip[], key: string): string {
  return findChipByKey(chips, key)?.domainRaw || '';
}

export function resolveFilterContext(chips: FilterChip[], key: string): Dict {
  return findChipByKey(chips, key)?.context || {};
}

export function resolveFilterContextRaw(chips: FilterChip[], key: string): string {
  return findChipByKey(chips, key)?.contextRaw || '';
}

export function normalizeDomain(domain: unknown): unknown[] {
  return Array.isArray(domain) ? domain : [];
}

export function mergeSceneDomain(base: unknown, sceneFilters: unknown): unknown[] {
  const baseDomain = normalizeDomain(base);
  const sceneDomain = normalizeDomain(sceneFilters);
  if (!sceneDomain.length) return baseDomain;
  if (!baseDomain.length) return sceneDomain;
  return [...sceneDomain, ...baseDomain];
}

export function mergeActiveFilter(base: unknown, options: { hasActiveField: boolean; filterValue: 'all' | 'active' | 'archived' }): unknown[] {
  const domain = normalizeDomain(base);
  if (!options.hasActiveField || options.filterValue === 'all') return domain;
  const activeClause = ['active', '=', options.filterValue === 'active'];
  if (!domain.length) return [activeClause];
  return [...domain, activeClause];
}

export function resolveEffectiveFilterDomain(contractDomain: unknown, savedDomain: unknown, groupDomain: unknown): unknown[] {
  return mergeSceneDomain(mergeSceneDomain(contractDomain, savedDomain), groupDomain);
}

export function resolveEffectiveFilterDomainRaw(contractRaw: string, savedRaw: string): string {
  return [contractRaw, savedRaw].filter(Boolean).join(' && ');
}

export function resolveEffectiveFilterContext(contractContext: Dict, savedContext: Dict): Dict {
  return { ...contractContext, ...savedContext };
}

export function resolveEffectiveFilterContextRaw(contractContextRaw: string, savedContextRaw: string): string {
  return [contractContextRaw, savedContextRaw].filter(Boolean).join(' && ');
}

export function resolveGroupByContext(chips: GroupByChip[], field: string): Dict {
  if (!field) return {};
  const found = findGroupByChip(chips, field);
  return { ...(found?.context || {}), group_by: field };
}

export function resolveGroupByContextRaw(chips: GroupByChip[], field: string): string {
  if (!field) return '';
  const found = findGroupByChip(chips, field);
  return [found?.contextRaw || '', `{'group_by': '${field}'}`].filter(Boolean).join(' && ');
}

export function resolveEffectiveRequestContext(filterContext: Dict, groupContext: Dict): Dict {
  return { ...filterContext, ...groupContext };
}

export function resolveEffectiveRequestContextRaw(filterContextRaw: string, groupContextRaw: string): string {
  return [filterContextRaw, groupContextRaw].filter(Boolean).join(' && ');
}

export function mergeRequestContext(options: {
  base: Dict | string | undefined;
  extra?: Dict;
  routeContext: Dict;
  menuId?: number;
}): Dict {
  const mergedExtra = options.extra || {};
  const menuId = Number(options.menuId || 0);
  if (!options.base || typeof options.base === 'string') {
    return menuId > 0
      ? { menu_id: menuId, ...options.routeContext, ...mergedExtra }
      : { ...options.routeContext, ...mergedExtra };
  }
  if (menuId <= 0) {
    return { ...options.base, ...options.routeContext, ...mergedExtra };
  }
  return { ...options.base, menu_id: menuId, ...options.routeContext, ...mergedExtra };
}

export function readTotalFromListResult(payload: unknown): number | null {
  if (!payload || typeof payload !== 'object') return null;
  const raw = Number((payload as Dict).total);
  if (!Number.isFinite(raw) || raw < 0) return null;
  return Math.trunc(raw);
}
