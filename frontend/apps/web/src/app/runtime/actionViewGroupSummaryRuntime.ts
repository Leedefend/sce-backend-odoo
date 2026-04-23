type Dict = Record<string, unknown>;

type GroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
};

export function mapActionViewGroupSummaryItems(options: {
  groupSummaryRaw: unknown;
  emptyLabel: string;
  maxItems?: number;
  buildGroupKey: (field: unknown, value: unknown, label: string) => string;
}): GroupSummaryItem[] {
  const rows = Array.isArray(options.groupSummaryRaw) ? (options.groupSummaryRaw as Dict[]) : [];
  const maxItems = Number(options.maxItems || 12) > 0 ? Number(options.maxItems || 12) : 12;
  return rows
    .map((row) => {
      const label = String(row.label ?? row.value ?? options.emptyLabel).trim() || options.emptyLabel;
      const backendGroupKey = String(row.group_key || '').trim();
      return {
        key: backendGroupKey || options.buildGroupKey(row.field, row.value, label),
        label,
        count: Number(row.count || 0),
        domain: Array.isArray(row.domain) ? row.domain : [],
        value: row.value,
      };
    })
    .filter((item) => item.count >= 0)
    .slice(0, maxItems);
}

export function resolveActionViewGroupWindowMetrics(options: {
  groupPagingRaw: unknown;
  effectiveGroupOffset: number;
  summaryLength: number;
}): {
  groupWindowCount: number;
  groupWindowStart: number;
  groupWindowEnd: number;
  groupWindowTotal: number | null;
  groupWindowNextOffset: number | null;
  groupWindowPrevOffset: number | null;
} {
  const groupPaging = options.groupPagingRaw && typeof options.groupPagingRaw === 'object'
    ? (options.groupPagingRaw as Dict)
    : {};
  const windowCount = Number.isFinite(Number(groupPaging.group_count))
    ? Math.max(0, Math.trunc(Number(groupPaging.group_count)))
    : options.summaryLength;
  const groupWindowStart = Number.isFinite(Number(groupPaging.window_start))
    ? Math.max(0, Math.trunc(Number(groupPaging.window_start)))
    : windowCount > 0
      ? options.effectiveGroupOffset + 1
      : 0;
  const groupWindowEnd = Number.isFinite(Number(groupPaging.window_end))
    ? Math.max(0, Math.trunc(Number(groupPaging.window_end)))
    : windowCount > 0
      ? options.effectiveGroupOffset + windowCount
      : 0;
  const groupWindowTotal = Number.isFinite(Number(groupPaging.group_total))
    ? Math.max(0, Math.trunc(Number(groupPaging.group_total)))
    : null;
  const groupWindowNextOffset = Number.isFinite(Number(groupPaging.next_group_offset))
    ? Math.max(0, Math.trunc(Number(groupPaging.next_group_offset)))
    : groupPaging.has_more
      ? options.effectiveGroupOffset + Math.max(1, options.summaryLength || windowCount || 0)
      : null;
  const groupWindowPrevOffset = Number.isFinite(Number(groupPaging.prev_group_offset))
    ? Math.max(0, Math.trunc(Number(groupPaging.prev_group_offset)))
    : options.effectiveGroupOffset > 0
      ? Math.max(0, options.effectiveGroupOffset - Math.max(1, options.summaryLength || windowCount || 1))
      : null;
  return {
    groupWindowCount: windowCount,
    groupWindowStart,
    groupWindowEnd,
    groupWindowTotal,
    groupWindowNextOffset,
    groupWindowPrevOffset,
  };
}
