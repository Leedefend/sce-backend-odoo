type Dict = Record<string, unknown>;

const DEFAULT_ACTION_VIEW_LIMIT = 20;
const LEGACY_ACTION_VIEW_DEFAULT_LIMIT = 80;

export function resolveActionViewSortSeed(options: {
  currentSortRaw?: unknown;
  sceneReadyDefaultSortRaw?: unknown;
  sceneDefaultSortRaw?: unknown;
  searchDefaultOrderRaw?: unknown;
  viewOrderRaw?: unknown;
  metaOrderRaw?: unknown;
  fallbackSortRaw?: unknown;
}): string {
  const currentSort = String(options.currentSortRaw || '').trim();
  if (currentSort) return currentSort;
  const candidates = [
    options.sceneReadyDefaultSortRaw,
    options.sceneDefaultSortRaw,
    options.searchDefaultOrderRaw,
    options.viewOrderRaw,
    options.metaOrderRaw,
    options.fallbackSortRaw,
  ];
  for (const item of candidates) {
    const value = String(item || '').trim();
    if (value) return value;
  }
  return '';
}

export function resolveActionViewContractLimit(limitRaw?: unknown): number {
  const normalized = Number(limitRaw || DEFAULT_ACTION_VIEW_LIMIT);
  if (!Number.isFinite(normalized) || normalized <= 0) return DEFAULT_ACTION_VIEW_LIMIT;
  const limit = Math.min(Math.trunc(normalized), 200);
  return limit === LEGACY_ACTION_VIEW_DEFAULT_LIMIT ? DEFAULT_ACTION_VIEW_LIMIT : limit;
}

export function buildActionViewListRequest(options: {
  model: string;
  requestedFields: string[];
  domain: unknown[];
  domainRaw: unknown;
  activeGroupByField: string;
  listOffset: number;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  context: Dict;
  contextRaw: unknown;
  searchTerm: string;
  order: string;
}): Dict {
  const grouped = Boolean(options.activeGroupByField);
  return {
    model: options.model,
    fields: options.requestedFields.length ? options.requestedFields : ['id', 'name'],
    domain: options.domain,
    domain_raw: options.domainRaw,
    need_total: true,
    need_aggregates: true,
    group_by: grouped ? options.activeGroupByField : undefined,
    group_offset: grouped ? Math.max(0, Math.trunc(options.groupWindowOffset || 0)) : 0,
    need_group_total: grouped,
    group_sample_limit: options.groupSampleLimit,
    group_limit: Math.min(50, Math.max(12, Number(options.contractLimit || 0))),
    group_page_size: options.groupSampleLimit,
    group_page_offsets: options.groupPageOffsets,
    context: options.context,
    context_raw: options.contextRaw,
    limit: options.contractLimit,
    offset: Math.max(0, Math.trunc(options.listOffset || 0)),
    search_term: options.searchTerm.trim() || undefined,
    order: options.order.trim() || undefined,
  };
}
