type Dict = Record<string, unknown>;

export function resolveActionViewRecordId(rawId: unknown): number | string | null {
  if (typeof rawId === 'number') return rawId;
  if (typeof rawId === 'string' && rawId.trim()) return rawId;
  return null;
}

export function buildActionViewRowClickTarget(options: {
  targetModel: string;
  rawId: unknown;
  menuId: number;
  actionId: number;
  carryQuery: Dict;
}): { path: string; query: Dict } | null {
  if (!options.targetModel) return null;
  const recordId = resolveActionViewRecordId(options.rawId);
  if (recordId === null) return null;
  return {
    path: `/r/${options.targetModel}/${recordId}`,
    query: {
      menu_id: options.menuId || undefined,
      action_id: options.actionId || undefined,
      ...options.carryQuery,
    },
  };
}

export function resolveListControlTransition(options: {
  control: 'search' | 'sort' | 'filter';
  value: string;
}): {
  nextSearchTerm: string | null;
  nextSortValue: string | null;
  nextFilterValue: 'all' | 'active' | 'archived' | null;
  nextGroupWindowOffset: number;
  shouldClearSelection: boolean;
} {
  return {
    nextSearchTerm: options.control === 'search' ? options.value : null,
    nextSortValue: options.control === 'sort' ? options.value : null,
    nextFilterValue: options.control === 'filter' ? (options.value as 'all' | 'active' | 'archived') : null,
    nextGroupWindowOffset: 0,
    shouldClearSelection: options.control === 'filter',
  };
}

export function resolveSelectionAfterToggle(options: {
  selectedIds: number[];
  id: number;
  selected: boolean;
}): number[] {
  const set = new Set(options.selectedIds);
  if (options.selected) {
    set.add(options.id);
  } else {
    set.delete(options.id);
  }
  return Array.from(set);
}

export function resolveSelectionAfterToggleAll(options: {
  selectedIds: number[];
  ids: number[];
  selected: boolean;
}): number[] {
  if (!options.ids.length) return options.selectedIds;
  const set = new Set(options.selectedIds);
  options.ids.forEach((id) => {
    if (options.selected) set.add(id);
    else set.delete(id);
  });
  return Array.from(set);
}
