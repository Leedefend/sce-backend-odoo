type Dict = Record<string, unknown>;

function asObject(value: unknown): Dict {
  return value && typeof value === 'object' ? (value as Dict) : {};
}

function asText(value: unknown): string {
  return String(value || '').trim();
}

export function resolveActionViewGroupPagingState(options: {
  resultDataRaw: unknown;
  fallbackGroupWindowOffset: number;
}): {
  resultData: Dict;
  groupPaging: Dict;
  effectiveGroupOffset: number;
  groupWindowId: string;
  responseGroupFingerprint: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
} {
  const resultData = asObject(options.resultDataRaw);
  const groupPaging = asObject(resultData.group_paging);
  const windowIdentity = asObject(groupPaging.window_identity);

  const rawOffset = Number(groupPaging.group_offset);
  const effectiveGroupOffset = Number.isFinite(rawOffset)
    ? Math.max(0, Math.trunc(rawOffset))
    : Math.max(0, Math.trunc(Number(options.fallbackGroupWindowOffset || 0)));

  const groupWindowId = asText(windowIdentity.window_id) || asText(groupPaging.window_id);
  const responseGroupFingerprint = asText(windowIdentity.query_fingerprint) || asText(groupPaging.query_fingerprint);
  const groupWindowDigest = asText(windowIdentity.window_digest) || asText(groupPaging.window_digest);
  const groupWindowIdentityKey = asText(windowIdentity.key) || asText(groupPaging.window_key);

  return {
    resultData,
    groupPaging,
    effectiveGroupOffset,
    groupWindowId,
    responseGroupFingerprint,
    groupWindowDigest,
    groupWindowIdentityKey,
  };
}
