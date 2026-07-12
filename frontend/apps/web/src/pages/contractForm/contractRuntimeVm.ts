export function collectRuntimeCapabilities(session: {
  capabilities?: unknown[];
  capabilityCatalog?: Record<string, { key?: unknown; state?: unknown; capability_state?: unknown }>;
}) {
  const out = new Set<string>();
  (session.capabilities || []).forEach((key) => {
    const normalized = String(key || '').trim();
    if (normalized) out.add(normalized);
  });
  Object.values(session.capabilityCatalog || {}).forEach((meta) => {
    const key = String(meta?.key || '').trim();
    if (!key) return;
    const state = String(meta?.state || '').trim().toUpperCase();
    const capState = String(meta?.capability_state || '').trim().toLowerCase();
    if (state === 'LOCKED' || capState === 'deny') return;
    out.add(key);
  });
  return out;
}

export function collectRuntimeUserGroups(user: { groups_xmlids?: unknown } | null | undefined) {
  return Array.isArray(user?.groups_xmlids)
    ? user.groups_xmlids.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
}

export function normalizeContractWarnings(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      if (typeof row === 'string') return row;
      if (row && typeof row === 'object') {
        return String((row as Record<string, unknown>).message || (row as Record<string, unknown>).code || '');
      }
      return '';
    })
    .map((item) => item.trim())
    .filter((item) => Boolean(item) && !item.startsWith('access_policy:'));
}

export function normalizeSearchFilters(rows: unknown) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const item = row && typeof row === 'object' && !Array.isArray(row)
        ? row as Record<string, unknown>
        : {};
      return {
        key: String(item.key || '').trim(),
        label: String(item.label || item.key || '').trim(),
        domainRaw: String(item.domain_raw || '').trim(),
        contextRaw: String(item.context_raw || '').trim(),
      };
    })
    .filter((row) => row.key && row.label);
}
