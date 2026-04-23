import { normalizeGroupPageOffset, serializeGroupPageOffsets } from './actionViewGroupWindowRuntime';

type GroupedRowShape = {
  key: string;
  label: string;
  pageLimit?: number;
  count?: number;
};

type GroupSummaryShape = {
  label: string;
};

export function normalizeGroupedRouteCollections(options: {
  groupedRows: GroupedRowShape[];
  groupSummaryItems: GroupSummaryShape[];
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
  routeGroupValue: string;
  groupSampleLimit: number;
}): {
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
  collapsedChanged: boolean;
  groupPageChanged: boolean;
  groupValueExists: boolean;
} {
  const validGroupKeys = new Set(options.groupedRows.map((item) => item.key).filter(Boolean));
  const normalizedCollapsed = options.collapsedGroupKeys.filter((key) => validGroupKeys.has(key));
  const collapsedChanged =
    normalizedCollapsed.length !== options.collapsedGroupKeys.length
    || normalizedCollapsed.some((key, idx) => key !== options.collapsedGroupKeys[idx]);

  const groupValueExists = !options.routeGroupValue
    || options.groupedRows.some((item) => item.label === options.routeGroupValue)
    || options.groupSummaryItems.some((item) => item.label === options.routeGroupValue);

  const normalizedGroupPages = Object.entries(options.groupPageOffsets).reduce<Record<string, number>>((acc, [key, offset]) => {
    if (!validGroupKeys.has(key)) return acc;
    const grouped = options.groupedRows.find((item) => item.key === key);
    if (!grouped) return acc;
    const pageLimit = Math.max(1, Number(grouped.pageLimit || options.groupSampleLimit || 3));
    const normalizedOffset = normalizeGroupPageOffset(Number(offset || 0), pageLimit, Number(grouped.count || 0));
    if (normalizedOffset > 0) acc[key] = normalizedOffset;
    return acc;
  }, {});

  const groupPageChanged =
    Object.keys(normalizedGroupPages).length !== Object.keys(options.groupPageOffsets).length
    || Object.entries(normalizedGroupPages).some(([key, value]) => options.groupPageOffsets[key] !== value);

  return {
    normalizedCollapsed,
    normalizedGroupPages,
    collapsedChanged,
    groupPageChanged,
    groupValueExists,
  };
}

export function buildNormalizedGroupedRoutePatch(options: {
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
  groupWindowOffset: number;
  groupValueExists: boolean;
}): Record<string, unknown> {
  const nextState: Record<string, unknown> = {
    group_collapsed: options.normalizedCollapsed.length ? options.normalizedCollapsed.join(',') : undefined,
    group_page: serializeGroupPageOffsets(options.normalizedGroupPages) || undefined,
    group_offset: options.groupWindowOffset > 0 ? options.groupWindowOffset : undefined,
  };
  if (!options.groupValueExists) nextState.group_value = undefined;
  return nextState;
}

export function hasGroupedRouteOffsetChanged(routeGroupOffsetRaw: unknown, groupWindowOffset: number): boolean {
  const routeGroupOffset = Number(routeGroupOffsetRaw || 0);
  const currentOffset = Number.isFinite(routeGroupOffset) && routeGroupOffset > 0 ? Math.trunc(routeGroupOffset) : 0;
  return currentOffset !== groupWindowOffset;
}
