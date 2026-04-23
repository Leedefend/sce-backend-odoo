import { resolveRequestedFields, type ActionViewListProfileShape } from './actionViewRequestRuntime';

export function resolveGroupedPageFieldsFromColumns(requested: string[], fallbackColumns: string[]): string[] {
  const base = requested.length ? requested : fallbackColumns;
  const dedup = Array.from(new Set((base.length ? base : ['id', 'name']).map((item) => String(item || '').trim()).filter(Boolean)));
  if (!dedup.includes('id')) dedup.unshift('id');
  return dedup;
}

export function resolveGroupedPageFields(options: {
  contractFields: string[];
  profile: ActionViewListProfileShape | null;
  fallbackColumns: string[];
}): string[] {
  const requested = resolveRequestedFields(options.contractFields, options.profile);
  return resolveGroupedPageFieldsFromColumns(requested, options.fallbackColumns);
}

export function normalizeGroupedPageLimit(rawLimit: unknown, fallbackLimit: number): number {
  const candidate = Number(rawLimit || fallbackLimit || 3);
  if (!Number.isFinite(candidate) || candidate <= 0) return 3;
  return Math.min(Math.trunc(candidate), 50);
}

export function resolveGroupedPageWindow(totalCountRaw: unknown, pageOffsetRaw: unknown, pageLimit: number) {
  const totalCount = Math.max(0, Number(totalCountRaw || 0));
  const pageOffset = Math.max(0, Number(pageOffsetRaw || 0));
  const nextCurrent = Math.floor(pageOffset / pageLimit) + 1;
  const nextTotal = Math.max(1, Math.ceil(totalCount / pageLimit));
  const nextRangeStart = totalCount > 0 ? pageOffset + 1 : 0;
  const nextRangeEnd = totalCount > 0 ? Math.min(totalCount, pageOffset + pageLimit) : 0;
  return {
    pageCurrent: nextCurrent,
    pageTotal: nextTotal,
    pageRangeStart: nextRangeStart,
    pageRangeEnd: nextRangeEnd,
    pageHasPrev: pageOffset > 0,
    pageHasNext: pageOffset + pageLimit < totalCount,
  };
}

export function buildGroupedRowsListRequest(options: {
  model: string;
  fields: string[];
  domain: unknown[];
  context: Record<string, unknown>;
  contextRaw: string;
  limit: number;
  offset: number;
  order: string;
}): Record<string, unknown> {
  return {
    model: options.model,
    fields: options.fields,
    domain: options.domain,
    context: options.context,
    context_raw: options.contextRaw,
    limit: options.limit,
    offset: options.offset,
    order: options.order,
  };
}

export function buildGroupedRowsPatchedState(options: {
  base: Record<string, unknown>;
  rows: Array<Record<string, unknown>>;
  offset: number;
  limit: number;
  count: number;
}): Record<string, unknown> {
  const pageWindow = resolveGroupedPageWindow(options.count, options.offset, options.limit);
  return {
    ...options.base,
    sampleRows: options.rows,
    pageOffset: options.offset,
    pageLimit: options.limit,
    pageCurrent: pageWindow.pageCurrent,
    pageTotal: pageWindow.pageTotal,
    pageRangeStart: pageWindow.pageRangeStart,
    pageRangeEnd: pageWindow.pageRangeEnd,
    pageWindow: { start: pageWindow.pageRangeStart, end: pageWindow.pageRangeEnd },
    pageHasPrev: pageWindow.pageHasPrev,
    pageHasNext: pageWindow.pageHasNext,
    pageSyncedFromServer: true,
    loading: false,
  };
}
