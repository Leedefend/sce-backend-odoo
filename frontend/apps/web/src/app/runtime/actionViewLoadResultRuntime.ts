type Dict = Record<string, unknown>;

export type ActionViewGroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
};

export type ActionViewGroupedRow = {
  key: string;
  label: string;
  count: number;
  sampleRows: Array<Record<string, unknown>>;
  domain?: unknown[];
  pageOffset: number;
  pageLimit: number;
  pageCurrent?: number;
  pageTotal?: number;
  pageRangeStart?: number;
  pageRangeEnd?: number;
  pageWindow?: { start?: number; end?: number };
  pageHasPrev?: boolean;
  pageHasNext?: boolean;
  pageSyncedFromServer?: boolean;
  loading?: boolean;
};

export function resolveActionViewRecords(resultDataRaw: unknown): Array<Record<string, unknown>> {
  const resultData = resultDataRaw && typeof resultDataRaw === 'object' ? (resultDataRaw as Dict) : {};
  return Array.isArray(resultData.records) ? (resultData.records as Array<Record<string, unknown>>) : [];
}

export function resolveActionViewGroupedRowsRaw(resultDataRaw: unknown): Array<Record<string, unknown>> {
  const resultData = resultDataRaw && typeof resultDataRaw === 'object' ? (resultDataRaw as Dict) : {};
  return Array.isArray(resultData.grouped_rows) ? (resultData.grouped_rows as Array<Record<string, unknown>>) : [];
}

export function mapActionViewGroupedRows(options: {
  groupedRowsRaw: Array<Record<string, unknown>>;
  groupPagingRaw: unknown;
  groupSampleLimit: number;
  groupPageOffsets: Record<string, number>;
  emptyLabel: string;
  maxItems?: number;
  buildGroupKey: (field: unknown, value: unknown, fallback: unknown) => string;
  normalizeGroupPageOffset: (offset: number, limit: number, total: number) => number;
}): ActionViewGroupedRow[] {
  const groupPaging = options.groupPagingRaw && typeof options.groupPagingRaw === 'object'
    ? (options.groupPagingRaw as Dict)
    : {};
  const fallbackPageSize = Number(groupPaging.page_size || 0) || options.groupSampleLimit || 3;
  const maxItems = Number(options.maxItems || 12) > 0 ? Number(options.maxItems || 12) : 12;
  return options.groupedRowsRaw
    .map((item) => {
      const label = String(item.label ?? item.value ?? options.emptyLabel).trim() || options.emptyLabel;
      const fallbackKey = options.buildGroupKey(item.field, item.value, label);
      const key = String(item.group_key || fallbackKey);
      const pageLimit = Math.max(1, Number((item.page_size ?? item.page_limit) || fallbackPageSize));
      const pageOffsetRaw = Number((item.page_applied_offset ?? item.page_offset ?? options.groupPageOffsets[key]) || 0);
      return {
        key,
        label,
        count: Number(item.count || 0),
        domain: Array.isArray(item.domain) ? item.domain : [],
        sampleRows: Array.isArray(item.sample_rows) ? (item.sample_rows as Array<Record<string, unknown>>) : [],
        pageOffset: options.normalizeGroupPageOffset(pageOffsetRaw, pageLimit, Number(item.count || 0)),
        pageLimit,
        pageCurrent: Number(item.page_current || 0) > 0 ? Number(item.page_current || 0) : undefined,
        pageTotal: Number(item.page_total || 0) > 0 ? Number(item.page_total || 0) : undefined,
        pageRangeStart: Number(item.page_range_start || 0) >= 0 ? Number(item.page_range_start || 0) : undefined,
        pageRangeEnd: Number(item.page_range_end || 0) >= 0 ? Number(item.page_range_end || 0) : undefined,
        pageWindow: typeof item.page_window === 'object' && item.page_window !== null
          ? {
            start: Number((item.page_window as Dict).start || 0) >= 0 ? Number((item.page_window as Dict).start || 0) : undefined,
            end: Number((item.page_window as Dict).end || 0) >= 0 ? Number((item.page_window as Dict).end || 0) : undefined,
          }
          : undefined,
        pageHasPrev: typeof item.page_has_prev === 'boolean' ? Boolean(item.page_has_prev) : undefined,
        pageHasNext: typeof item.page_has_next === 'boolean' ? Boolean(item.page_has_next) : undefined,
        pageSyncedFromServer: Object.prototype.hasOwnProperty.call(item, 'page_offset')
          || Object.prototype.hasOwnProperty.call(item, 'page_applied_offset')
          || Object.prototype.hasOwnProperty.call(item, 'page_clamped')
          || Object.prototype.hasOwnProperty.call(item, 'page_limit')
          || Object.prototype.hasOwnProperty.call(item, 'page_size'),
        loading: false,
      };
    })
    .filter((item) => item.sampleRows.length > 0)
    .slice(0, maxItems);
}

export function resolveActionViewActiveGroupSummaryKey(options: {
  currentActiveKey: string;
  routeGroupValueRaw: unknown;
  summaryItems: ActionViewGroupSummaryItem[];
}): string {
  const current = String(options.currentActiveKey || '').trim();
  if (current) return current;
  const routeGroupValue = String(options.routeGroupValueRaw || '').trim();
  if (!routeGroupValue) return '';
  const matched = options.summaryItems.find((item) => item.label === routeGroupValue);
  return matched ? matched.key : '';
}

export function reconcileActionViewSelectedIds(options: {
  selectedIds: number[];
  records: Array<Record<string, unknown>>;
}): number[] {
  const currentIds = new Set(
    options.records
      .map((row) => {
        const id = row.id;
        if (typeof id === 'number') return id;
        if (typeof id === 'string' && id.trim()) {
          const parsed = Number(id);
          return Number.isNaN(parsed) ? null : parsed;
        }
        return null;
      })
      .filter((id): id is number => typeof id === 'number'),
  );
  return options.selectedIds.filter((id) => currentIds.has(id));
}

