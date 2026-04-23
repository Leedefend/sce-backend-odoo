export function parseGroupPageOffsets(raw: string): Record<string, number> {
  const out: Record<string, number> = {};
  if (!raw) return out;
  raw.split(';').forEach((pair) => {
    const [rawKey, rawOffset] = pair.split(':');
    const key = decodeURIComponent(String(rawKey || '').trim());
    const offset = Number(rawOffset || 0);
    if (!key) return;
    if (!Number.isFinite(offset) || offset < 0) return;
    out[key] = Math.trunc(offset);
  });
  return out;
}

export function serializeGroupPageOffsets(state: Record<string, number>): string {
  return Object.entries(state || {})
    .filter(([key, offset]) => key && Number.isFinite(offset) && offset >= 0)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, offset]) => `${encodeURIComponent(key)}:${Math.trunc(offset)}`)
    .join(';');
}

export function normalizeGroupPageOffset(offset: number, pageLimit: number, totalCount: number): number {
  const limit = Math.max(1, Math.trunc(pageLimit || 1));
  const safeTotal = Math.max(0, Math.trunc(totalCount || 0));
  const maxOffset = safeTotal > 0 ? Math.max(0, Math.floor((safeTotal - 1) / limit) * limit) : 0;
  const safeOffset = Number.isFinite(offset) ? Math.max(0, Math.trunc(offset)) : 0;
  return Math.min(safeOffset, maxOffset);
}

type Dict = Record<string, unknown>;

export function buildGroupWindowRouteSyncPlan(options: {
  activeGroupByField: string;
  effectiveGroupOffset: number;
  responseGroupFingerprint: string;
  routeGroupFingerprint: string;
  routeGroupWindowId: string;
  routeGroupWindowDigest: string;
  routeGroupWindowIdentityKey: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
}): {
  resetPatch: Dict | null;
  syncPatches: Dict[];
} {
  const activeGroupByField = String(options.activeGroupByField || '').trim();
  if (!activeGroupByField) return { resetPatch: null, syncPatches: [] };

  const resetSeed: Dict = {
    group_offset: undefined,
    group_page: undefined,
    group_collapsed: undefined,
  };

  if (
    options.routeGroupFingerprint
    && options.responseGroupFingerprint
    && options.routeGroupFingerprint !== options.responseGroupFingerprint
    && options.effectiveGroupOffset > 0
  ) {
    return {
      resetPatch: {
        ...resetSeed,
        group_fp: options.responseGroupFingerprint,
        group_wid: undefined,
        group_wdg: undefined,
        group_wik: undefined,
      },
      syncPatches: [],
    };
  }

  if (
    options.routeGroupWindowId
    && options.groupWindowId
    && options.routeGroupWindowId !== options.groupWindowId
    && options.effectiveGroupOffset > 0
  ) {
    return {
      resetPatch: {
        ...resetSeed,
        group_wid: options.groupWindowId,
        group_wdg: undefined,
        group_wik: undefined,
      },
      syncPatches: [],
    };
  }

  if (
    options.routeGroupWindowDigest
    && options.groupWindowDigest
    && options.routeGroupWindowDigest !== options.groupWindowDigest
    && options.effectiveGroupOffset > 0
  ) {
    return {
      resetPatch: {
        ...resetSeed,
        group_wdg: options.groupWindowDigest,
      },
      syncPatches: [],
    };
  }

  if (
    options.routeGroupWindowIdentityKey
    && options.groupWindowIdentityKey
    && options.routeGroupWindowIdentityKey !== options.groupWindowIdentityKey
    && options.effectiveGroupOffset > 0
  ) {
    return {
      resetPatch: {
        ...resetSeed,
        group_wik: options.groupWindowIdentityKey,
      },
      syncPatches: [],
    };
  }

  const syncPatches: Dict[] = [];

  if (
    options.responseGroupFingerprint
    && options.routeGroupFingerprint !== options.responseGroupFingerprint
    && options.effectiveGroupOffset <= 0
  ) {
    syncPatches.push({
      group_fp: options.responseGroupFingerprint,
      group_wid: options.groupWindowId || undefined,
      group_wdg: options.groupWindowDigest || undefined,
      group_wik: options.groupWindowIdentityKey || undefined,
    });
  } else if (!options.responseGroupFingerprint && options.routeGroupFingerprint) {
    syncPatches.push({ group_fp: undefined });
  }

  if (options.routeGroupWindowId !== (options.groupWindowId || '')) {
    syncPatches.push({ group_wid: options.groupWindowId || undefined });
  }
  if (options.routeGroupWindowDigest !== (options.groupWindowDigest || '')) {
    syncPatches.push({ group_wdg: options.groupWindowDigest || undefined });
  }
  if (options.routeGroupWindowIdentityKey !== (options.groupWindowIdentityKey || '')) {
    syncPatches.push({ group_wik: options.groupWindowIdentityKey || undefined });
  }

  return { resetPatch: null, syncPatches };
}

export function mergeGroupWindowSyncPatches(patches: Dict[]): Dict | null {
  if (!Array.isArray(patches) || patches.length === 0) return null;
  const merged = patches.reduce<Dict>((acc, patch) => ({
    ...acc,
    ...(patch || {}),
  }), {});
  return Object.keys(merged).length ? merged : null;
}
