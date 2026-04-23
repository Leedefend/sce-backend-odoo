import { resolveSelectionAfterToggle, resolveSelectionAfterToggleAll } from './actionViewInteractionRuntime';

export function resolveClearSelectionState(): number[] {
  return [];
}

export function resolveAssigneeSelectionState(options: {
  assigneeId: number | null;
}): number | null {
  return options.assigneeId;
}

export function resolveToggleSelectionState(options: {
  selectedIds: number[];
  id: number;
  selected: boolean;
}): number[] {
  return resolveSelectionAfterToggle({
    selectedIds: options.selectedIds,
    id: options.id,
    selected: options.selected,
  });
}

export function resolveToggleSelectionAllState(options: {
  selectedIds: number[];
  ids: number[];
  selected: boolean;
}): number[] {
  return resolveSelectionAfterToggleAll({
    selectedIds: options.selectedIds,
    ids: options.ids,
    selected: options.selected,
  });
}

export function resolveIfMatchMapState(options: {
  ids: number[];
  records: Array<Record<string, unknown>>;
}): Record<number, string> {
  const wanted = new Set(options.ids);
  const map: Record<number, string> = {};
  options.records.forEach((row) => {
    const rawId = row.id;
    const id =
      typeof rawId === 'number'
        ? rawId
        : typeof rawId === 'string' && rawId.trim()
          ? Number(rawId)
          : NaN;
    if (!Number.isFinite(id) || !wanted.has(id)) return;
    const etag = typeof row.write_date === 'string' ? row.write_date : '';
    if (!etag) return;
    map[id] = etag;
  });
  return map;
}
