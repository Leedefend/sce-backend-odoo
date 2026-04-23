type Dict = Record<string, unknown>;

export function buildActionViewGroupRouteSyncPayload(options: {
  activeGroupByField: string;
  effectiveGroupOffset: number;
  routeSnapshot: Dict;
  responseGroupFingerprint: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
}): {
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
} {
  return {
    activeGroupByField: options.activeGroupByField,
    effectiveGroupOffset: options.effectiveGroupOffset,
    responseGroupFingerprint: options.responseGroupFingerprint,
    routeGroupFingerprint: String(options.routeSnapshot.groupFingerprintRaw || '').trim(),
    routeGroupWindowId: String(options.routeSnapshot.groupWindowIdRaw || '').trim(),
    routeGroupWindowDigest: String(options.routeSnapshot.groupWindowDigestRaw || '').trim(),
    routeGroupWindowIdentityKey: String(options.routeSnapshot.groupWindowIdentityKeyRaw || '').trim(),
    groupWindowId: options.groupWindowId,
    groupWindowDigest: options.groupWindowDigest,
    groupWindowIdentityKey: options.groupWindowIdentityKey,
  };
}

