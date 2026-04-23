import { buildGroupedRowsPatchedState, normalizeGroupedPageLimit } from './actionViewGroupedRowsRuntime';
import type { GroupedRow } from './actionViewGroupRuntimeState';

export function resolveGroupedRowsPageChangeTarget(options: {
  rows: GroupedRow[];
  groupKey: string;
  requestedOffset: unknown;
  requestedLimit: unknown;
  sampleLimitFallback: number;
  normalizeOffset: (offset: number, limit: number, total: number) => number;
}): {
  found: GroupedRow | null;
  pageLimit: number;
  nextOffset: number;
  shouldSkip: boolean;
} {
  const found = options.rows.find((item) => item.key === options.groupKey) || null;
  if (!found) {
    return { found: null, pageLimit: 0, nextOffset: 0, shouldSkip: true };
  }
  const pageLimit = normalizeGroupedPageLimit(options.requestedLimit || found.pageLimit, options.sampleLimitFallback);
  const nextOffset = options.normalizeOffset(Number(options.requestedOffset || 0), pageLimit, Number(found.count || 0));
  const shouldSkip = nextOffset === found.pageOffset && found.sampleRows.length > 0;
  return { found, pageLimit, nextOffset, shouldSkip };
}

export function setGroupedRowsLoadingByKeys(rows: GroupedRow[], keys: Set<string>): GroupedRow[] {
  return rows.map((item) => (keys.has(item.key) ? { ...item, loading: true } : item));
}

export function applyGroupedRowsPageChangeSuccess(options: {
  rows: GroupedRow[];
  groupKey: string;
  payloadRows: Array<Record<string, unknown>>;
  nextOffset: number;
  pageLimit: number;
  totalCount: number;
}): GroupedRow[] {
  return options.rows.map((item) =>
    item.key === options.groupKey
      ? (buildGroupedRowsPatchedState({
        base: item,
        rows: options.payloadRows,
        offset: options.nextOffset,
        limit: options.pageLimit,
        count: options.totalCount,
      }) as GroupedRow)
      : item,
  );
}

export function resolveGroupedRowsHydrateCandidates(rows: GroupedRow[]): GroupedRow[] {
  return rows.filter((item) => Number(item.pageOffset || 0) > 0 && !item.pageSyncedFromServer);
}

export function applyGroupedRowsHydrateResults(options: {
  rows: GroupedRow[];
  updates: Array<{ key: string; rows: Array<Record<string, unknown>>; ok: boolean }>;
}): GroupedRow[] {
  const updateMap = new Map(options.updates.map((row) => [row.key, row]));
  return options.rows.map((item) => {
    const found = updateMap.get(item.key);
    if (!found) return item;
    if (!found.ok) return { ...item, loading: false };
    return { ...item, sampleRows: found.rows, loading: false };
  });
}

export function resolveGroupedRowsHydrateGuard(options: {
  targetModel: string;
  candidatesLength: number;
}): { ok: true } | { ok: false } {
  if (!options.targetModel) return { ok: false };
  if (options.candidatesLength <= 0) return { ok: false };
  return { ok: true };
}

export function resolveGroupedRowsHydrateKeys(candidates: GroupedRow[]): Set<string> {
  return new Set(candidates.map((item) => item.key));
}

export function resolveGroupedRowsHydratePageState(options: {
  pageLimitRaw: unknown;
  pageOffsetRaw: unknown;
  countRaw: unknown;
  sampleLimitFallback: number;
  normalizeOffset: (offset: number, limit: number, total: number) => number;
}): {
  limit: number;
  offset: number;
} {
  const limit = Math.max(1, Number(options.pageLimitRaw || options.sampleLimitFallback || 3));
  const offset = options.normalizeOffset(Number(options.pageOffsetRaw || 0), limit, Number(options.countRaw || 0));
  return { limit, offset };
}

export function resolveGroupedRowsHydrateUpdateSuccess(options: {
  key: string;
  resultDataRaw: unknown;
}): { key: string; rows: Array<Record<string, unknown>>; ok: boolean } {
  const data = options.resultDataRaw && typeof options.resultDataRaw === 'object'
    ? (options.resultDataRaw as Record<string, unknown>)
    : {};
  return {
    key: options.key,
    rows: Array.isArray(data.records) ? (data.records as Array<Record<string, unknown>>) : [],
    ok: true,
  };
}

export function resolveGroupedRowsHydrateUpdateFailure(options: {
  key: string;
}): { key: string; rows: Array<Record<string, unknown>>; ok: boolean } {
  return {
    key: options.key,
    rows: [],
    ok: false,
  };
}

export function resolveGroupedRowsPageChangeGuard(options: {
  groupKey: string;
  found: GroupedRow | null;
  shouldSkip: boolean;
  targetModel: string;
}): { ok: true } | { ok: false } {
  if (!options.groupKey) return { ok: false };
  if (!options.found || options.shouldSkip) return { ok: false };
  if (!options.targetModel) return { ok: false };
  return { ok: true };
}

export function resolveGroupedRowsPageDomain(domainRaw: unknown): unknown[] {
  return Array.isArray(domainRaw) ? domainRaw : [];
}

export function resolveGroupedRowsPagePayloadRows(resultDataRaw: unknown): Array<Record<string, unknown>> {
  const data = resultDataRaw && typeof resultDataRaw === 'object'
    ? (resultDataRaw as Record<string, unknown>)
    : {};
  return Array.isArray(data.records) ? (data.records as Array<Record<string, unknown>>) : [];
}

export function resolveGroupedRowsPageOffsetState(options: {
  groupPageOffsets: Record<string, number>;
  groupKey: string;
  nextOffset: number;
  serializeGroupPageOffsets: (value: Record<string, number>) => string;
}): {
  nextGroupPageOffsets: Record<string, number>;
  groupPageQueryValue: string | undefined;
} {
  const nextGroupPageOffsets = { ...options.groupPageOffsets, [options.groupKey]: options.nextOffset };
  return {
    nextGroupPageOffsets,
    groupPageQueryValue: options.serializeGroupPageOffsets(nextGroupPageOffsets) || undefined,
  };
}

export function applyGroupedRowsPageChangeFailure(options: {
  rows: GroupedRow[];
  groupKey: string;
}): GroupedRow[] {
  return options.rows.map((item) => (item.key === options.groupKey ? { ...item, loading: false } : item));
}
